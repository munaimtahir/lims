from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SampleCollectionViewSet

router = DefaultRouter()
router.register(r"", SampleCollectionViewSet, basename="sample")

urlpatterns = [
    path("", include(router.urls)),
]
