"""URL configuration for results app."""

from django.urls import path

from .views import (
    ResultDetailView,
    ResultListCreateView,
    enter_result,
    publish_result,
    verify_result,
)

urlpatterns = [
    path("", ResultListCreateView.as_view(), name="result-list-create"),
    path("<int:pk>/", ResultDetailView.as_view(), name="result-detail"),
    path("<int:pk>/enter/", enter_result, name="result-enter"),
    path("<int:pk>/verify/", verify_result, name="result-verify"),
    path("<int:pk>/publish/", publish_result, name="result-publish"),
]
