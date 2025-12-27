"""
Models for analyzer integration.
"""

from django.db import models
from django.conf import settings


class Analyzer(models.Model):
    """
    Represents a laboratory analyzer device.
    
    Attributes:
        name (str): Name of the analyzer.
        model (str): Model number/identifier.
        manufacturer (str): Manufacturer name.
        connection_type (str): Connection type (HL7, FTP, API, etc.).
        connection_config (JSON): Configuration for connection.
        is_active (bool): Whether analyzer is currently active.
        last_sync_at (datetime, optional): Last successful sync timestamp.
        created_at (datetime): When analyzer was registered.
    """
    
    CONNECTION_TYPES = [
        ("HL7", "HL7"),
        ("FTP", "FTP"),
        ("API", "REST API"),
        ("FILE", "File Upload"),
    ]
    
    name = models.CharField(max_length=255)
    model = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    connection_type = models.CharField(
        max_length=20,
        choices=CONNECTION_TYPES,
        default="HL7",
    )
    connection_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Connection configuration (host, port, credentials, etc.)",
    )
    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "analyzers"
        verbose_name = "Analyzer"
        verbose_name_plural = "Analyzers"
        ordering = ["name"]
    
    def __str__(self):
        """Return string representation."""
        return f"{self.name} ({self.model})"


class AnalyzerResultImport(models.Model):
    """
    Represents an imported result from an analyzer.
    
    Attributes:
        analyzer (Analyzer): The analyzer that generated this result.
        raw_message (str): Raw HL7 or data message from analyzer.
        parsed_data (JSON): Parsed result data.
        order_item (OrderItem, optional): Associated order item if matched.
        test_result (TestResult, optional): Created test result.
        status (str): Import status.
        error_message (str, optional): Error message if import failed.
        imported_at (datetime): When result was imported.
        imported_by (User, optional): User who processed the import.
    """
    
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("MATCHED", "Matched to Order"),
        ("IMPORTED", "Imported Successfully"),
        ("FAILED", "Import Failed"),
        ("MANUAL_REVIEW", "Requires Manual Review"),
    ]
    
    analyzer = models.ForeignKey(
        Analyzer,
        on_delete=models.CASCADE,
        related_name="imports",
    )
    raw_message = models.TextField(help_text="Raw message/data from analyzer")
    parsed_data = models.JSONField(
        default=dict,
        help_text="Parsed result data",
    )
    order_item = models.ForeignKey(
        "orders.OrderItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analyzer_imports",
    )
    test_result = models.ForeignKey(
        "results.TestResult",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analyzer_import",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )
    error_message = models.TextField(blank=True, null=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analyzer_imports",
    )
    
    class Meta:
        db_table = "analyzer_result_imports"
        verbose_name = "Analyzer Result Import"
        verbose_name_plural = "Analyzer Result Imports"
        ordering = ["-imported_at"]
        indexes = [
            models.Index(fields=["status", "imported_at"]),
            models.Index(fields=["analyzer", "status"]),
        ]
    
    def __str__(self):
        """Return string representation."""
        return f"Import from {self.analyzer.name} - {self.status}"

