from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestCategoryViewSet, TestViewSet, TestPanelViewSet

router = DefaultRouter()
router.register(r'categories', TestCategoryViewSet)
router.register(r'tests', TestViewSet)
router.register(r'panels', TestPanelViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
