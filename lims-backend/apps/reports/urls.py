from django.urls import include, path
from rest_framework.routers import DefaultRouter


from .views import ReportViewSet
from .views_analytics import AnalyticsViewSet

router = DefaultRouter()
router.register(r"", ReportViewSet, basename="report")

urlpatterns = [
    # Analytics Endpoints
    path("overview/", AnalyticsViewSet.as_view({"get": "overview"}), name="analytics-overview"),
    path("patients/", AnalyticsViewSet.as_view({"get": "patients"}), name="analytics-patients"),
    path("tests/", AnalyticsViewSet.as_view({"get": "tests"}), name="analytics-tests"),
    path("referrals/", AnalyticsViewSet.as_view({"get": "referrals"}), name="analytics-referrals"),
    path("finance/", AnalyticsViewSet.as_view({"get": "finance"}), name="analytics-finance"),
    path("export/", AnalyticsViewSet.as_view({"post": "export_report"}), name="analytics-export"),

    path("", include(router.urls)),
]

