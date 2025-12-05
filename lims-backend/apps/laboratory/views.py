from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import TestCategory, Test, TestPanel
from .serializers import (
    TestCategorySerializer,
    TestSerializer,
    TestPanelSerializer
)


class TestCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Test Categories.
    """
    queryset = TestCategory.objects.all()
    serializer_class = TestCategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']


class TestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Tests.
    """
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['test_name', 'test_code', 'loinc_code']
    ordering_fields = ['test_code', 'test_name', 'price']


class TestPanelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations for Test Panels.
    """
    queryset = TestPanel.objects.all()
    serializer_class = TestPanelSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['panel_name', 'panel_code']
    ordering_fields = ['panel_code', 'panel_name', 'price']
