"""
Serializers for integrations app.
"""

from rest_framework import serializers
from .models import Analyzer, AnalyzerResultImport


class AnalyzerSerializer(serializers.ModelSerializer):
    """
    Serializer for Analyzer model.
    """
    
    class Meta:
        model = Analyzer
        fields = [
            "id",
            "name",
            "model",
            "manufacturer",
            "connection_type",
            "connection_config",
            "is_active",
            "last_sync_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "last_sync_at"]


class AnalyzerResultImportSerializer(serializers.ModelSerializer):
    """
    Serializer for AnalyzerResultImport model.
    """
    
    analyzer_name = serializers.CharField(source="analyzer.name", read_only=True)
    order_id = serializers.CharField(source="order_item.order.order_id", read_only=True)
    test_name = serializers.CharField(
        source="order_item.test.test_name",
        read_only=True,
    )
    imported_by_name = serializers.CharField(
        source="imported_by.full_name",
        read_only=True,
    )
    
    class Meta:
        model = AnalyzerResultImport
        fields = [
            "id",
            "analyzer",
            "analyzer_name",
            "raw_message",
            "parsed_data",
            "order_item",
            "order_id",
            "test_name",
            "test_result",
            "status",
            "error_message",
            "imported_at",
            "imported_by",
            "imported_by_name",
        ]
        read_only_fields = ["imported_at", "test_result"]

