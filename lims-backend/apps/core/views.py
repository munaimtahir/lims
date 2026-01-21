"""
Views for core models.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.db import connection
from .models import SystemSettings
from .serializers import SystemSettingsSerializer
from apps.accounts.permissions import IsAdminOrReadOnly


# Image upload configuration constants
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
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
    http_method_names = ['get', 'put', 'patch', 'post', 'delete', 'options', 'head']
    
    def get_object(self):
        """Get the singleton settings instance."""
        return SystemSettings.get_settings()
    
    def list(self, request, *args, **kwargs):
        """Return the singleton settings instance."""
        # Handle PUT/PATCH on list endpoint for singleton pattern
        if request.method == 'PUT':
            return self.update(request, *args, **kwargs)
        elif request.method == 'PATCH':
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
            return Response({
                "status": "healthy",
                "service": "LIMS Backend",
                "database": "connected"
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "unhealthy",
                "service": "LIMS Backend",
                "database": "disconnected"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
