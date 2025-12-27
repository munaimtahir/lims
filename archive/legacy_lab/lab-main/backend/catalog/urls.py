"""URL configuration for catalog app."""

from django.urls import path

from .views import (
    ParameterDetailView,
    ParameterListCreateView,
    ParameterQuickTextDetailView,
    ParameterQuickTextListCreateView,
    ReferenceRangeDetailView,
    ReferenceRangeListCreateView,
    TestCatalogDetailView,
    TestCatalogListCreateView,
    TestDetailView,
    TestListCreateView,
    TestParameterDetailView,
    TestParameterListCreateView,
)

urlpatterns = [
    # TestCatalog (legacy)
    path("", TestCatalogListCreateView.as_view(), name="test-catalog-list"),
    path("<int:pk>/", TestCatalogDetailView.as_view(), name="test-catalog-detail"),
    # Tests (LIMS Master)
    path("tests/", TestListCreateView.as_view(), name="test-list"),
    path("tests/<int:pk>/", TestDetailView.as_view(), name="test-detail"),
    # Parameters
    path("parameters/", ParameterListCreateView.as_view(), name="parameter-list"),
    path(
        "parameters/<int:pk>/", ParameterDetailView.as_view(), name="parameter-detail"
    ),
    # Test-Parameter Relationships
    path(
        "test-parameters/",
        TestParameterListCreateView.as_view(),
        name="test-parameter-list",
    ),
    path(
        "test-parameters/<int:pk>/",
        TestParameterDetailView.as_view(),
        name="test-parameter-detail",
    ),
    # Reference Ranges
    path(
        "reference-ranges/",
        ReferenceRangeListCreateView.as_view(),
        name="reference-range-list",
    ),
    path(
        "reference-ranges/<int:pk>/",
        ReferenceRangeDetailView.as_view(),
        name="reference-range-detail",
    ),
    # Parameter Quick Texts
    path(
        "quick-texts/",
        ParameterQuickTextListCreateView.as_view(),
        name="quick-text-list",
    ),
    path(
        "quick-texts/<int:pk>/",
        ParameterQuickTextDetailView.as_view(),
        name="quick-text-detail",
    ),
]
