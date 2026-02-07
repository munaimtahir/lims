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
    created_from = django_filters.DateFilter(method="filter_created_from")
    created_to = django_filters.DateFilter(method="filter_created_to")

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
            models.Q(first_name__icontains=value)
            | models.Q(last_name__icontains=value)
            | models.Q(full_name__icontains=value)
        )

    def filter_age_min(self, queryset, name, value):
        """Filter by minimum age."""
        from datetime import date, timedelta

        # Convert to int if Decimal
        age = int(value) if hasattr(value, "__int__") else value
        # Calculate max DOB: someone who is at least 'age' years old
        # was born on or before (today - age years)
        today = date.today()
        max_dob = date(today.year - age, today.month, today.day)
        # Handle leap year edge case (Feb 29)
        try:
            max_dob = date(today.year - age, today.month, today.day)
        except ValueError:
            # If Feb 29 doesn't exist in that year, use Feb 28
            max_dob = date(today.year - age, today.month, today.day - 1)
        return queryset.filter(date_of_birth__lte=max_dob)

    def filter_age_max(self, queryset, name, value):
        """Filter by maximum age."""
        from datetime import date

        # Convert to int if Decimal
        age = int(value) if hasattr(value, "__int__") else value
        # Calculate min DOB: someone who is at most 'age' years old
        # was born on or after (today - age - 1 years)
        today = date.today()
        min_dob = date(today.year - age - 1, today.month, today.day)
        # Handle leap year edge case
        try:
            min_dob = date(today.year - age - 1, today.month, today.day)
        except ValueError:
            # If Feb 29 doesn't exist in that year, use Feb 28
            min_dob = date(today.year - age - 1, today.month, today.day - 1)
        return queryset.filter(date_of_birth__gte=min_dob)

    def filter_created_from(self, queryset, name, value):
        """Filter by created_from date (start of day)."""
        from datetime import datetime
        from datetime import time as time_class

        import pytz
        from django.utils import timezone

        # Convert string to date if needed
        if isinstance(value, str):
            from datetime import date as date_class

            value = date_class.fromisoformat(value)
        # Convert date to start of day datetime in UTC
        # Since timezone.now() returns UTC, we should compare in UTC
        start_of_day_naive = datetime.combine(value, time_class.min)
        # Make timezone-aware using UTC to match timezone.now() behavior
        start_of_day = timezone.make_aware(start_of_day_naive, pytz.UTC)
        return queryset.filter(created_at__gte=start_of_day)

    def filter_created_to(self, queryset, name, value):
        """Filter by created_to date (end of day)."""
        from datetime import datetime
        from datetime import time as time_class
        from datetime import timedelta

        from django.utils import timezone

        # Convert string to date if needed
        if isinstance(value, str):
            from datetime import date as date_class

            value = date_class.fromisoformat(value)
        # Convert date to end of day in the current timezone
        # Get current timezone-aware datetime for today to determine timezone
        tz = timezone.get_current_timezone()
        end_of_day = timezone.make_aware(datetime.combine(value, time_class.max), tz)
        # Add 1 day and subtract 1 microsecond to get end of day
        end_of_day = end_of_day + timedelta(days=1) - timedelta(microseconds=1)
        return queryset.filter(created_at__lte=end_of_day)
