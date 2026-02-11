"""
Views for the Audit app.
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsAuditReader

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs.

    Only managers and admins can view audit logs.
    This ViewSet is read-only.
    """

    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAuditReader]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "actor",
        "entity_type",
        "entity_id",
        "action",
        "source",
        "created_at",
    ]
    search_fields = ["entity_type", "action", "notes"]
    ordering_fields = ["created_at", "timestamp", "action"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        entity_type = self.request.query_params.get("entity_type")
        entity_id = self.request.query_params.get("entity_id")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if entity_type:
            qs = qs.filter(entity_type=entity_type)
        if entity_id:
            qs = qs.filter(entity_id=str(entity_id))
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs
