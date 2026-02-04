"""
Tests for catalog import/export functionality, specifically testing the Phase C fixes:
- Column alias support
- Null value handling (NA, N/A, etc.)
- Decimal JSON serialization
- Header validation
"""

import pytest
from decimal import Decimal
from io import BytesIO
import openpyxl

from apps.laboratory.catalog_io import (
    normalize_header,
    apply_column_aliases,
    get_headers,
    is_null_value,
    safe_get,
    to_int,
    to_decimal,
    to_bool,
    _serialize_for_json,
    _validate_sheet_headers,
    COLUMN_ALIASES,
    NULL_VALUES,
    CATALOG_COLUMNS,
    import_catalog_from_excel,
)


class TestNormalizeHeader:
    """Tests for header normalization."""
    
    def test_basic_normalization(self):
        assert normalize_header("Test ID") == "test_id"
        assert normalize_header("test_id") == "test_id"
        assert normalize_header("TEST_ID") == "test_id"
    
    def test_parentheses_removal(self):
        assert normalize_header("Turnaround Time (hours)") == "turnaround_time_hours"
        assert normalize_header("Age Min (years)") == "age_min_years"
    
    def test_whitespace_handling(self):
        assert normalize_header("  test id  ") == "test_id"
        assert normalize_header("test   id") == "test___id"


class TestColumnAliases:
    """Tests for column alias functionality."""
    
    def test_tat_hours_alias(self):
        headers = {"tat_hours": 5}
        aliased = apply_column_aliases(headers)
        assert "turnaround_time" in aliased
        assert aliased["turnaround_time"] == 5
    
    def test_multiple_aliases(self):
        headers = {
            "test_id": 0,
            "tat_hours": 1,
            "sample_volume_ml": 2,
            "field_type": 3,
        }
        aliased = apply_column_aliases(headers)
        assert aliased["turnaround_time"] == 1
        assert aliased["sample_volume"] == 2
        assert aliased["data_type"] == 3
    
    def test_canonical_column_not_overwritten(self):
        """If both alias and canonical exist, canonical takes precedence."""
        headers = {
            "tat_hours": 5,
            "turnaround_time": 10,
        }
        aliased = apply_column_aliases(headers)
        assert aliased["turnaround_time"] == 10  # Original value preserved
    
    def test_reference_range_aliases(self):
        headers = {
            "age_min_years": 0,
            "age_max_years": 1,
            "ref_min": 2,
            "ref_max": 3,
        }
        aliased = apply_column_aliases(headers)
        assert aliased["age_min"] == 0
        assert aliased["age_max"] == 1
        assert aliased["reference_min"] == 2
        assert aliased["reference_max"] == 3


class TestNullValueHandling:
    """Tests for null value detection."""
    
    def test_none_is_null(self):
        assert is_null_value(None) is True
    
    def test_empty_string_is_null(self):
        assert is_null_value("") is True
        assert is_null_value("   ") is True
    
    def test_na_variants_are_null(self):
        for val in ["NA", "na", "N/A", "n/a", "#N/A", "#NA"]:
            assert is_null_value(val) is True, f"Expected {val!r} to be null"
    
    def test_null_string_is_null(self):
        for val in ["null", "NULL", "Null", "none", "None", "nil"]:
            assert is_null_value(val) is True, f"Expected {val!r} to be null"
    
    def test_dash_is_null(self):
        assert is_null_value("-") is True
        assert is_null_value("--") is True
        assert is_null_value(".") is True
    
    def test_regular_values_not_null(self):
        assert is_null_value("Hello") is False
        assert is_null_value("123") is False
        assert is_null_value(123) is False
        assert is_null_value(0) is False  # Zero is not null
        assert is_null_value(False) is False  # Boolean False is not null


class TestToInt:
    """Tests for integer conversion with null handling."""
    
    def test_basic_conversion(self):
        assert to_int(24) == 24
        assert to_int("24") == 24
    
    def test_float_to_int(self):
        assert to_int(24.0) == 24
        assert to_int("24.0") == 24
        assert to_int("24.5") == 24  # Truncates
    
    def test_null_values_return_none(self):
        assert to_int(None) is None
        assert to_int("") is None
        assert to_int("NA") is None
        assert to_int("N/A") is None
    
    def test_invalid_values_return_none(self):
        assert to_int("abc") is None
        assert to_int("12.34.56") is None


class TestToDecimal:
    """Tests for decimal conversion with null handling."""
    
    def test_basic_conversion(self):
        assert to_decimal("100.50") == Decimal("100.50")
        assert to_decimal(100) == Decimal("100")
    
    def test_null_values_return_none(self):
        assert to_decimal(None) is None
        assert to_decimal("NA") is None
        assert to_decimal("-") is None


class TestToBool:
    """Tests for boolean conversion with null handling."""
    
    def test_boolean_passthrough(self):
        assert to_bool(True) is True
        assert to_bool(False) is False
    
    def test_string_conversion(self):
        assert to_bool("true") is True
        assert to_bool("TRUE") is True
        assert to_bool("1") is True
        assert to_bool("yes") is True
        assert to_bool("false") is False
        assert to_bool("0") is False
        assert to_bool("no") is False
    
    def test_null_returns_default(self):
        assert to_bool(None, default=True) is True
        assert to_bool("NA", default=False) is False
        assert to_bool("", default=None) is None


class TestSerializeForJson:
    """Tests for JSON serialization helper."""
    
    def test_decimal_to_string(self):
        result = _serialize_for_json({"price": Decimal("100.50")})
        assert result["price"] == "100.50"
        assert isinstance(result["price"], str)
    
    def test_nested_decimals(self):
        result = _serialize_for_json({
            "data": [
                {"price": Decimal("100")},
                {"price": Decimal("200.50")},
            ]
        })
        assert result["data"][0]["price"] == "100"
        assert result["data"][1]["price"] == "200.50"
    
    def test_mixed_types(self):
        result = _serialize_for_json({
            "count": 5,
            "name": "test",
            "price": Decimal("100"),
            "active": True,
        })
        assert result["count"] == 5
        assert result["name"] == "test"
        assert result["price"] == "100"
        assert result["active"] is True


class TestValidateSheetHeaders:
    """Tests for header validation."""
    
    def test_all_required_present(self):
        headers = {"test_id": 0, "test_code": 1, "test_name": 2, "category": 3}
        warnings = []
        missing = _validate_sheet_headers("Tests", headers, ["test_id", "test_code"], warnings)
        assert missing == []
    
    def test_missing_required(self):
        headers = {"test_id": 0}
        warnings = []
        missing = _validate_sheet_headers("Tests", headers, ["test_id", "test_code"], warnings)
        assert "test_code" in missing
    
    def test_unknown_headers_warning(self):
        headers = {"test_id": 0, "test_code": 1, "unknown_col": 2}
        warnings = []
        _validate_sheet_headers("Tests", headers, ["test_id"], warnings)
        assert len(warnings) > 0
        assert "unknown_col" in warnings[0]["message"]


@pytest.fixture
def create_test_workbook():
    """Factory for creating test Excel workbooks."""
    def _create(sheets_data):
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        for sheet_name, rows in sheets_data.items():
            sheet = wb.create_sheet(sheet_name)
            for row in rows:
                sheet.append(row)
        
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer
    
    return _create


class TestImportWithAliases:
    """Integration tests for import with column aliases."""
    
    def test_import_with_tat_hours_column(self, create_test_workbook, db):
        """Verify tat_hours is correctly aliased to turnaround_time."""
        from apps.laboratory.models import TestCategory
        
        # Create a workbook with tat_hours instead of turnaround_time
        wb_data = {
            "Tests": [
                ["test_id", "test_code", "test_name", "category", "tat_hours", "price"],
                [1, "TST1", "Test One", "General", 24, 100],
            ],
            "Parameters": [
                ["parameter_id", "parameter_name"],
                ["p1", "Param One"],
            ],
            "Mapping": [
                ["test_id", "parameter_id"],
                [1, "p1"],
            ],
        }
        
        buffer = create_test_workbook(wb_data)
        
        result = import_catalog_from_excel(
            buffer,
            strict=True,
            allow_defaults=True,  # Enable defaults
            mode="upsert",
            dry_run=True,
        )
        
        # Should succeed even though column is named tat_hours
        assert len(result["errors"]) == 0, f"Unexpected errors: {result['errors']}"
        assert result["counts"]["tests"]["created"] == 1
    
    def test_import_with_na_values(self, create_test_workbook, db):
        """Verify NA values are treated as None."""
        wb_data = {
            "Tests": [
                ["test_id", "test_code", "test_name", "category", "turnaround_time", "loinc_code"],
                [1, "TST1", "Test One", "General", 24, "NA"],
                [2, "TST2", "Test Two", "General", 24, "N/A"],
                [3, "TST3", "Test Three", "General", 24, "-"],
            ],
            "Parameters": [
                ["parameter_id", "parameter_name"],
                ["p1", "Param One"],
            ],
            "Mapping": [
                ["test_id", "parameter_id"],
                [1, "p1"],
            ],
        }
        
        buffer = create_test_workbook(wb_data)
        
        result = import_catalog_from_excel(
            buffer,
            strict=True,
            allow_defaults=True,
            mode="upsert",
            dry_run=True,
        )
        
        # All three tests should be valid (NA treated as None, which is OK for optional fields)
        assert result["counts"]["tests"]["created"] == 3
        assert len(result["errors"]) == 0


class TestRegressionGoodFile:
    """Regression tests to ensure the good file still imports correctly."""
    
    def test_import_ready_file_parses(self, db):
        """The LIMS_TestCatalog_IMPORT_READY.xlsx should still work."""
        import os
        
        test_file = os.path.join(os.path.dirname(__file__), 
                                 "../../../LIMS_TestCatalog_IMPORT_READY.xlsx")
        
        if not os.path.exists(test_file):
            pytest.skip("Test file not found")
        
        with open(test_file, 'rb') as f:
            result = import_catalog_from_excel(
                f,
                strict=True,
                allow_defaults=True,
                mode="upsert",
                dry_run=True,
            )
        
        # Should have tests created
        assert result["counts"]["tests"]["created"] > 0 or result["counts"]["tests"]["unchanged"] > 0
        # Should not have JSON serialization errors (verified by calling this)
        import json
        json.dumps(result)  # This will raise if Decimal isn't serialized
