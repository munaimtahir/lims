from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DispatchViewSet, OrderItemViewSet, OrderViewSet

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"order-items", OrderItemViewSet, basename="orderitem")
router.register(r"dispatches", DispatchViewSet, basename="dispatch")

urlpatterns = [
    path("", include(router.urls)),
]
