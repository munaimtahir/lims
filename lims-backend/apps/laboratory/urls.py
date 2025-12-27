from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TestCategoryViewSet,
    TestViewSet,
    TestPanelViewSet,
    TestParameterViewSet,
    ReferenceRangeViewSet,
)

router = DefaultRouter()
router.register(r"categories", TestCategoryViewSet)
router.register(r"tests", TestViewSet)
router.register(r"panels", TestPanelViewSet)
router.register(r"parameters", TestParameterViewSet)
router.register(r"reference-ranges", ReferenceRangeViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
