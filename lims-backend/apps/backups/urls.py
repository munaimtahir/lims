from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BackupArtifactViewSet

router = DefaultRouter()
router.register(r"", BackupArtifactViewSet, basename="backup")

urlpatterns = [
    path("", include(router.urls)),
]
