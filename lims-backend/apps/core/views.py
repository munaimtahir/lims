"""
Views for core models.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.db import connection
from .models import SystemSettings
from .serializers import SystemSettingsSerializer
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

