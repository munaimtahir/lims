"""
Advanced filters for patient search.
"""

import django_filters
from django.db import models
from .models import Patient


class PatientFilter(django_filters.FilterSet):
    """
    Advanced filter for patients with multiple criteria.
    """
    
    # Date range filtering
    created_from = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")
    
    # Name search (multiple fields)
    name = django_filters.CharFilter(method="filter_name")
    
    # Age range
    age_min = django_filters.NumberFilter(method="filter_age_min")
    age_max = django_filters.NumberFilter(method="filter_age_max")
    
    # Gender
    gender = django_filters.ChoiceFilter(choices=Patient.GENDER_CHOICES)
    
    class Meta:
        model = Patient
        fields = ["phone", "national_id", "cnic", "gender"]
    
    def filter_name(self, queryset, name, value):
        """Filter by name across first_name, last_name, and full_name."""
        return queryset.filter(
            models.Q(first_name__icontains=value) |
            models.Q(last_name__icontains=value) |
            models.Q(full_name__icontains=value)
        )
    
    def filter_age_min(self, queryset, name, value):
        """Filter by minimum age."""
        from datetime import date
        max_dob = date.today().replace(year=date.today().year - value)
        return queryset.filter(date_of_birth__lte=max_dob)
    
    def filter_age_max(self, queryset, name, value):
        """Filter by maximum age."""
        from datetime import date
        min_dob = date.today().replace(year=date.today().year - value - 1)
        return queryset.filter(date_of_birth__gte=min_dob)

