"""URL configuration for orders app."""

from django.urls import path

from .views import OrderDetailView, OrderListCreateView, cancel_order, edit_order_tests

urlpatterns = [
    path("", OrderListCreateView.as_view(), name="order-list-create"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("<int:pk>/cancel/", cancel_order, name="order-cancel"),
    path("<int:pk>/edit-tests/", edit_order_tests, name="order-edit-tests"),
]
