"""
Tests for export utility functions.
"""
import pytest
from django.http import HttpResponse

from apps.core.export_utils import export_to_csv, export_to_excel


class TestExportToCSV:
    """Test export_to_csv function."""

    def test_export_dict_data_with_headers(self):
        """Test CSV export with dictionary data and explicit headers."""
        data = [
            {"name": "John", "age": 30, "city": "New York"},
            {"name": "Jane", "age": 25, "city": "Boston"},
        ]
        headers = ["name", "age", "city"]

        response = export_to_csv(data, "test.csv", headers)

        assert isinstance(response, HttpResponse)
        assert response["Content-Type"] == "text/csv"
        assert 'attachment; filename="test.csv"' in response["Content-Disposition"]

        # Check content
        content = response.content.decode("utf-8")
        assert "name" in content
        assert "John" in content
        assert "Jane" in content

    def test_export_dict_data_without_headers(self):
        """Test CSV export with dictionary data, auto-generate headers."""
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
        ]

        response = export_to_csv(data, "test.csv")

        assert isinstance(response, HttpResponse)
        content = response.content.decode("utf-8")
        assert "name" in content
        assert "age" in content

    def test_export_list_data_with_headers(self):
        """Test CSV export with list data and headers."""
        data = [
            ["John", 30, "New York"],
            ["Jane", 25, "Boston"],
        ]
        headers = ["name", "age", "city"]

        response = export_to_csv(data, "test.csv", headers)

        assert isinstance(response, HttpResponse)
        content = response.content.decode("utf-8")
        assert "name" in content
        assert "John" in content

    def test_export_list_data_without_headers(self):
        """Test CSV export with list data without headers."""
        data = [
            ["John", 30],
            ["Jane", 25],
        ]

        response = export_to_csv(data, "test.csv")

        assert isinstance(response, HttpResponse)
        content = response.content.decode("utf-8")
        assert "John" in content
        assert "30" in content

    def test_export_empty_data(self):
        """Test CSV export with empty data."""
        data = []

        response = export_to_csv(data, "empty.csv")

        assert isinstance(response, HttpResponse)
        assert response["Content-Type"] == "text/csv"

    def test_export_dict_with_missing_keys(self):
        """Test CSV export with dictionaries missing some keys."""
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "city": "Boston"},  # Missing age
        ]
        headers = ["name", "age", "city"]

        response = export_to_csv(data, "test.csv", headers)

        assert isinstance(response, HttpResponse)
        content = response.content.decode("utf-8")
        assert "John" in content
        assert "Jane" in content


class TestExportToExcel:
    """Test export_to_excel function."""

    def test_export_dict_data_with_headers(self):
        """Test Excel export with dictionary data and explicit headers."""
        data = [
            {"name": "John", "age": 30, "city": "New York"},
            {"name": "Jane", "age": 25, "city": "Boston"},
        ]
        headers = ["name", "age", "city"]

        response = export_to_excel(data, "test.xlsx", headers, "Test Sheet")

        assert isinstance(response, HttpResponse)
        assert (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in response["Content-Type"]
        )
        assert 'attachment; filename="test.xlsx"' in response["Content-Disposition"]
        assert len(response.content) > 0

    def test_export_dict_data_without_headers(self):
        """Test Excel export with dictionary data, auto-generate headers."""
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
        ]

        response = export_to_excel(data, "test.xlsx")

        assert isinstance(response, HttpResponse)
        assert len(response.content) > 0

    def test_export_list_data_with_headers(self):
        """Test Excel export with list data and headers."""
        data = [
            ["John", 30, "New York"],
            ["Jane", 25, "Boston"],
        ]
        headers = ["name", "age", "city"]

        response = export_to_excel(data, "test.xlsx", headers, "Test Sheet")

        assert isinstance(response, HttpResponse)
        assert len(response.content) > 0

    def test_export_list_data_without_headers(self):
        """Test Excel export with list data without headers."""
        data = [
            ["John", 30],
            ["Jane", 25],
        ]

        response = export_to_excel(data, "test.xlsx")

        assert isinstance(response, HttpResponse)
        assert len(response.content) > 0

    def test_export_empty_data(self):
        """Test Excel export with empty data."""
        data = []

        response = export_to_excel(data, "empty.xlsx")

        assert isinstance(response, HttpResponse)
        assert (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in response["Content-Type"]
        )
        assert len(response.content) > 0  # Excel file still created

    def test_export_dict_with_missing_keys(self):
        """Test Excel export with dictionaries missing some keys."""
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "city": "Boston"},  # Missing age
        ]
        headers = ["name", "age", "city"]

        response = export_to_excel(data, "test.xlsx", headers)

        assert isinstance(response, HttpResponse)
        assert len(response.content) > 0

    def test_export_custom_sheet_name(self):
        """Test Excel export with custom sheet name."""
        data = [["John", 30]]
        headers = ["name", "age"]

        response = export_to_excel(data, "test.xlsx", headers, "Custom Sheet")

        assert isinstance(response, HttpResponse)
        assert len(response.content) > 0

    def test_export_large_data(self):
        """Test Excel export with larger dataset."""
        data = [{"id": i, "value": f"Item {i}"} for i in range(100)]
        headers = ["id", "value"]

        response = export_to_excel(data, "large.xlsx", headers)

        assert isinstance(response, HttpResponse)
        assert len(response.content) > 0

    def test_export_with_special_characters(self):
        """Test Excel export with special characters in data."""
        data = [
            {"name": "José", "note": "Test & Value"},
            {"name": "María", "note": "Price: $100"},
        ]
        headers = ["name", "note"]

        response = export_to_excel(data, "special.xlsx", headers)

        assert isinstance(response, HttpResponse)
        assert len(response.content) > 0

    def test_export_column_width_adjustment(self):
        """Test that column widths are auto-adjusted."""
        data = [
            {
                "short": "A",
                "long": "This is a very long string that should trigger column width adjustment",
            },
        ]
        headers = ["short", "long"]

        response = export_to_excel(data, "widths.xlsx", headers)

        assert isinstance(response, HttpResponse)
        assert len(response.content) > 0

    def test_export_excel_with_non_string_cell_value(self):
        """Test Excel export handles non-string cell values in column width calculation."""
        # Create data that will trigger the except block in column width calculation
        # Use a value that causes an exception when trying to get length
        data = [
            {"col1": object(), "col2": "normal"},  # object() doesn't have len()
        ]
        headers = ["col1", "col2"]

        # Should not raise exception, should handle gracefully
        response = export_to_excel(data, "nonstring.xlsx", headers)
        assert isinstance(response, HttpResponse)
        assert len(response.content) > 0

    def test_export_excel_with_none_cell_value(self):
        """Test Excel export handles None cell values."""
        data = [
            {"col1": None, "col2": "normal"},
        ]
        headers = ["col1", "col2"]

        response = export_to_excel(data, "none.xlsx", headers)
        assert isinstance(response, HttpResponse)
        assert len(response.content) > 0
