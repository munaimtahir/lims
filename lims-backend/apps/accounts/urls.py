"""
URL patterns for accounts app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    # Auth endpoints
    path("login/", AuthViewSet.as_view({"post": "login"}), name="login"),
    path("logout/", AuthViewSet.as_view({"post": "logout"}), name="logout"),
    path("me/", AuthViewSet.as_view({"get": "me"}), name="me"),
    # User management
    path("", include(router.urls)),
]
