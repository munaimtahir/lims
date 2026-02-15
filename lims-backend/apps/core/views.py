"""
Views for core models.
"""

from django.db import connection
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets

from apps.core.authz import user_tenant
from apps.accounts.permissions import IsAdminOrReadOnly
from apps.core.services.settings import get_tenant_settings

from .models import Branch, CollectionCenter, PrintTemplate, SystemSettings, TenantSettings
from .serializers import (
    BranchSerializer,
    CollectionCenterSerializer,
    PrintTemplateSerializer,
    SystemSettingsSerializer,
    TenantSettingsSerializer,
)

# Image upload configuration constants
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/gif"]
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024  # 5MB in bytes


class SystemSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing system settings.

    Implements singleton pattern - only one settings instance exists.
    """

    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ["get", "put", "patch", "post", "delete", "options", "head"]

    def get_object(self):
        """Get the singleton settings instance."""
        return SystemSettings.get_settings()

    def list(self, request, *args, **kwargs):
        """Return the singleton settings instance."""
        # Handle PUT/PATCH on list endpoint for singleton pattern
        if request.method == "PUT":
            return self.update(request, *args, **kwargs)
        elif request.method == "PATCH":
            return self.partial_update(request, *args, **kwargs)

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update system settings."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        # Set updated_by
        if request.user.is_authenticated:
            serializer.save(updated_by=request.user)
        else:
            serializer.save()

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Partially update system settings."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Set updated_by
        if request.user.is_authenticated:
            serializer.save(updated_by=request.user)
        else:
            serializer.save()

        return Response(serializer.data)

    def _handle_image_upload(self, request, field_name):
        """
        Handle image upload or removal for a given field.

        Validates file type and size before accepting uploads.
        """
        instance = self.get_object()
        if request.method == "DELETE":
            field = getattr(instance, field_name)
            if field:
                field.delete(save=True)
            return Response(SystemSettingsSerializer(instance).data)

        image = request.FILES.get(field_name)
        if not image:
            return Response(
                {"error": f"{field_name} file is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file type
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            return Response(
                {"error": f"Invalid file type. Allowed types: JPEG, PNG, GIF"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file size
        if image.size > MAX_IMAGE_SIZE_BYTES:
            return Response(
                {"error": f"File size exceeds maximum limit of {MAX_IMAGE_SIZE_MB}MB"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        setattr(instance, field_name, image)
        instance.updated_by = request.user
        instance.save()
        return Response(SystemSettingsSerializer(instance).data)

    @action(
        detail=False,
        methods=["post", "delete"],
        url_path="report-header-image",
        parser_classes=[MultiPartParser, FormParser],
    )
    def report_header_image(self, request):
        """Upload or remove report header image."""
        return self._handle_image_upload(request, "report_header_image")

    @action(
        detail=False,
        methods=["post", "delete"],
        url_path="report-footer-image",
        parser_classes=[MultiPartParser, FormParser],
    )
    def report_footer_image(self, request):
        """Upload or remove report footer image."""
        return self._handle_image_upload(request, "report_footer_image")

    @action(detail=False, methods=["get"])
    def current(self, request):
        """Get current system settings (alias for list)."""
        return self.list(request)


class TenantSettingsView(APIView):
    """
    GET: Return tenant settings for the current user's tenant (create with defaults if missing).
    PATCH: Update tenant settings (admin only).
    """

    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get(self, request):
        tenant = user_tenant(request.user)
        settings = get_tenant_settings(tenant)
        if settings is None:
            return Response(
                {"detail": "No tenant assigned."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TenantSettingsSerializer(settings)
        return Response(serializer.data)

    def patch(self, request):
        tenant = user_tenant(request.user)
        settings_obj = get_tenant_settings(tenant)
        if settings_obj is None:
            return Response(
                {"detail": "No tenant assigned."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TenantSettingsSerializer(
            settings_obj, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        before = {f: getattr(settings_obj, f, None) for f in ["sample_workflow_enabled", "enable_collection_centers"]}
        serializer.save(updated_by=request.user)
        settings_obj.refresh_from_db()
        after = {f: getattr(settings_obj, f, None) for f in ["sample_workflow_enabled", "enable_collection_centers"]}
        try:
            from apps.audit.utils import emit_audit_event
            emit_audit_event(
                actor=request.user,
                entity_type="tenant_settings",
                entity_id=tenant.pk,
                action="TENANT_SETTINGS_UPDATED",
                before=before,
                after=after,
                metadata={"tenant_code": getattr(tenant, "code", None)},
                source="api",
            )
        except Exception:
            pass
        return Response(serializer.data)


class BranchViewSet(viewsets.ModelViewSet):
    """
    CRUD for branches (current user's tenant). Admin can add/edit/remove branches.
    """
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    serializer_class = BranchSerializer

    def get_queryset(self):
        tenant = user_tenant(self.request.user)
        if tenant is None:
            return Branch.objects.none()
        return Branch.objects.filter(tenant=tenant).order_by("code")

    def perform_create(self, serializer):
        tenant = user_tenant(self.request.user)
        if tenant is None:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": "No tenant assigned."})
        serializer.save(tenant=tenant)


class CollectionCenterViewSet(viewsets.ModelViewSet):
    """
    CRUD for collection centers. Admin can add/edit/remove collection centers.
    """
    queryset = CollectionCenter.objects.all().order_by("code")
    serializer_class = CollectionCenterSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring and container health checks.

    Returns 200 OK if the service is healthy, including database connectivity.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """Check service health."""
        try:
            # Check database connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_healthy = True
        except Exception:
            db_healthy = False

        if db_healthy:
            return Response(
                {
                    "status": "healthy",
                    "service": "LIMS Backend",
                    "database": "connected",
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "status": "unhealthy",
                    "service": "LIMS Backend",
                    "database": "disconnected",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class PrintTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing print templates.
    """

    queryset = PrintTemplate.objects.all()
    serializer_class = PrintTemplateSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        serializer.save()
