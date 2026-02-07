from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SampleViewSet

router = DefaultRouter()
router.register(r"", SampleViewSet, basename="sample")

urlpatterns = [
    path("", include(router.urls)),
]
