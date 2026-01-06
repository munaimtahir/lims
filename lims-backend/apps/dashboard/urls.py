from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardStatisticsViewSet

router = DefaultRouter()
router.register(r"statistics", DashboardStatisticsViewSet, basename="dashboard-statistics")

urlpatterns = [
    path("", include(router.urls)),
]
