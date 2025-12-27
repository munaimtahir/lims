"""URL configuration for samples app."""

from django.urls import path

from .views import (
    SampleDetailView,
    SampleListCreateView,
    collect_sample,
    receive_sample,
    reject_sample,
)

urlpatterns = [
    path("", SampleListCreateView.as_view(), name="sample-list-create"),
    path("<int:pk>/", SampleDetailView.as_view(), name="sample-detail"),
    path("<int:pk>/collect/", collect_sample, name="sample-collect"),
    path("<int:pk>/receive/", receive_sample, name="sample-receive"),
    path("<int:pk>/reject/", reject_sample, name="sample-reject"),
]
