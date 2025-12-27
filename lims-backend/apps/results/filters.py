"""
Advanced filters for result search.
"""

import django_filters
from decimal import Decimal
from django.db import models
from .models import TestResult


class TestResultFilter(django_filters.FilterSet):
    """
    Advanced filter for test results with value range search.
    """
    
    # Value range filtering (for numeric results)
    value_min = django_filters.NumberFilter(method="filter_value_min")
    value_max = django_filters.NumberFilter(method="filter_value_max")
    
    # Date range
    entered_from = django_filters.DateTimeFilter(field_name="entered_at", lookup_expr="gte")
    entered_to = django_filters.DateTimeFilter(field_name="entered_at", lookup_expr="lte")
    
    # Flag filtering
    flag = django_filters.ChoiceFilter(choices=TestResult.FLAG_CHOICES)
    
    # Status filtering
    status = django_filters.ChoiceFilter(choices=TestResult.VERIFICATION_STATUS)
    
    class Meta:
        model = TestResult
        fields = ["order_item", "test_parameter", "flag", "status"]
    
    def filter_value_min(self, queryset, name, value):
        """Filter by minimum numeric value."""
        # This is approximate - tries to parse result_value as float
        # For exact matching, would need to store numeric_value separately
        try:
            # Get all results and filter in Python (not ideal for large datasets)
            # In production, consider adding a numeric_value field to TestResult
            results = []
            for result in queryset:
                try:
                    num_val = float(result.result_value.replace(',', '').strip())
                    if num_val >= float(value):
                        results.append(result.id)
                except (ValueError, AttributeError):
                    pass
            return queryset.filter(id__in=results)
        except (ValueError, TypeError):
            return queryset.none()
    
    def filter_value_max(self, queryset, name, value):
        """Filter by maximum numeric value."""
        try:
            results = []
            for result in queryset:
                try:
                    num_val = float(result.result_value.replace(',', '').strip())
                    if num_val <= float(value):
                        results.append(result.id)
                except (ValueError, AttributeError):
                    pass
            return queryset.filter(id__in=results)
        except (ValueError, TypeError):
            return queryset.none()

