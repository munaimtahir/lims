"""Dashboard URL configuration."""

from django.urls import path

from .views import dashboard_analytics

urlpatterns = [
    path("analytics/", dashboard_analytics, name="dashboard-analytics"),
]
