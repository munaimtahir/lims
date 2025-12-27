"""
URL configuration for core app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LabTerminalViewSet, SystemSettingsViewSet

router = DefaultRouter()
router.register(r"terminals", LabTerminalViewSet, basename="terminal")
router.register(r"settings", SystemSettingsViewSet, basename="settings")

urlpatterns = [
    path("", include(router.urls)),
]

