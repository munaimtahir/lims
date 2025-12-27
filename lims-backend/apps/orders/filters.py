"""
Advanced filters for order search.
"""

import django_filters
from django.db import models
from .models import Order


class OrderFilter(django_filters.FilterSet):
    """
    Advanced filter for orders with date range, status, and priority.
    """
    
    # Date range filtering
    date_from = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")
    
    # Status filtering
    status = django_filters.ChoiceFilter(choices=Order.STATUS_CHOICES)
    
    # Priority filtering
    priority = django_filters.ChoiceFilter(choices=Order.PRIORITY_CHOICES)
    
    # Amount range
    amount_min = django_filters.NumberFilter(field_name="net_amount", lookup_expr="gte")
    amount_max = django_filters.NumberFilter(field_name="net_amount", lookup_expr="lte")
    
    # Payment status
    is_paid = django_filters.BooleanFilter()
    
    class Meta:
        model = Order
        fields = ["patient", "status", "priority", "is_paid"]

