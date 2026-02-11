"""
URL patterns for the Audit app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuditLogViewSet

router = DefaultRouter()
router.register(r"logs", AuditLogViewSet, basename="auditlog")

urlpatterns = [
    path("", AuditLogViewSet.as_view({"get": "list"}), name="auditlog-list-root"),
    path("", include(router.urls)),
]
