"""
URL configuration for LIMS project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.core.views import HealthCheckView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Health check endpoint (must be before other API routes)
    path('api/v1/health/', HealthCheckView.as_view(), name='health-check'),
    
    # API v1 (CSRF exempt - DRF handles authentication via JWT)
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/patients/', include('apps.patients.urls')),
    path('api/v1/laboratory/', include('apps.laboratory.urls')),
    path('api/v1/orders/', include('apps.orders.urls')),
    path('api/v1/samples/', include('apps.samples.urls')),
    path('api/v1/results/', include('apps.results.urls')),
    path('api/v1/reports/', include('apps.reports.urls')),
    path('api/v1/payments/', include('apps.billing.urls')),
    path('api/v1/audit/', include('apps.audit.urls')),
    path('api/v1/dashboard/', include('apps.dashboard.urls')),
    path('api/v1/core/', include('apps.core.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/integrations/', include('apps.integrations.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
