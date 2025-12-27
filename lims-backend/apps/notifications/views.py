"""
Views for notifications app.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing notifications (read-only).
    
    Notifications are created automatically by the system.
    """
    
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["notification_type", "status", "recipient_email"]
    search_fields = ["subject", "message", "recipient_email"]
    ordering_fields = ["created_at", "sent_at"]
    ordering = ["-created_at"]

