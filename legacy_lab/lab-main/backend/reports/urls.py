"""URL configuration for reports app."""

from django.urls import path

from .views import (
    ReportDetailView,
    ReportListView,
    download_report,
    generate_report,
)

urlpatterns = [
    path("", ReportListView.as_view(), name="report-list"),
    path("<int:pk>/", ReportDetailView.as_view(), name="report-detail"),
    path("generate/<int:order_id>/", generate_report, name="report-generate"),
    path("<int:pk>/download/", download_report, name="report-download"),
]
