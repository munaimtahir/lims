from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DashboardStatisticsViewSet

router = DefaultRouter()
router.register(
    r"statistics", DashboardStatisticsViewSet, basename="dashboard-statistics"
)

urlpatterns = [
    path("", include(router.urls)),
]
