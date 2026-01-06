"""
Views for core models.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
from .models import LabTerminal, SystemSettings
from .serializers import LabTerminalSerializer, SystemSettingsSerializer


class LabTerminalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Lab Terminals.
    
    Provides endpoints for managing laboratory terminals and their offline MRN ranges.
    """
    
    queryset = LabTerminal.objects.all()
    serializer_class = LabTerminalSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=["post"])
    def get_next_mrn(self, request, pk=None):
        """
        Get the next offline MRN from this terminal's range.
        
        This endpoint atomically allocates the next MRN from the terminal's
        reserved range for offline patient registration.
        
        Returns:
            Response: JSON with the next MRN number.
        """
        terminal = self.get_object()
        
        if not terminal.is_active:
            return Response(
                {"error": "Terminal is not active"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            next_mrn = terminal.get_next_offline_mrn()
            return Response(
                {
                    "terminal_code": terminal.code,
                    "next_mrn": next_mrn,
                    "range_start": terminal.offline_range_start,
                    "range_end": terminal.offline_range_end,
                    "remaining": terminal.offline_range_end - next_mrn + 1,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=["post"])
    def reset_range(self, request, pk=None):
        """
        Reset the offline MRN range for a terminal.
        
        This sets offline_current back to 0, allowing the range to be reused.
        Use with caution - only for testing or range reallocation.
        
        Requires admin permissions.
        """
        terminal = self.get_object()
        
        if not (request.user.is_admin or request.user.is_superuser):
            return Response(
                {"error": "Only administrators can reset terminal ranges"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        terminal.offline_current = 0
        terminal.save()
        
        return Response(
            {
                "status": "Range reset successfully",
                "terminal_code": terminal.code,
                "offline_current": terminal.offline_current,
            },
            status=status.HTTP_200_OK,
        )
    
    @action(detail=False, methods=["get"])
    def active(self, request):
        """
        Get all active terminals.
        """
        active_terminals = self.queryset.filter(is_active=True)
        page = self.paginate_queryset(active_terminals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(active_terminals, many=True)
        return Response(serializer.data)


class SystemSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing system settings.
    
    Implements singleton pattern - only one settings instance exists.
    """
    
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'patch', 'options', 'head']
    
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
    
    @action(detail=False, methods=["get"])
    def current(self, request):
        """Get current system settings (alias for list)."""
        return self.list(request)

