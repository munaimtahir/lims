"""
URL configuration for integrations app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnalyzerViewSet, AnalyzerResultImportViewSet

router = DefaultRouter()
router.register(r"analyzers", AnalyzerViewSet, basename="analyzer")
router.register(r"imports", AnalyzerResultImportViewSet, basename="analyzer-import")

urlpatterns = [
    path("", include(router.urls)),
]

