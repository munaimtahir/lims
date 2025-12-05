from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestResultViewSet

router = DefaultRouter()
router.register(r'', TestResultViewSet, basename='result')

urlpatterns = [
    path('', include(router.urls)),
]
