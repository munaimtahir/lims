"""
Tests for laboratory utility functions.
"""
import pytest
from decimal import Decimal
from io import BytesIO
from openpyxl import Workbook
from apps.laboratory.models import TestCategory, Test, TestParameter, ReferenceRange
from apps.laboratory.utils import import_tests_from_excel


@pytest.mark.django_db
class TestImportTestsFromExcel:
    """Test import_tests_from_excel utility function."""
    
    def test_import_tests_sheet(self):
        """Test importing tests from Excel Tests sheet."""
        # Create workbook with Tests sheet
        wb = Workbook()
        ws = wb.create_sheet("Tests")
        
        # Add header row
        ws.append(["Code", "Name", "Category", "SampleType", "Price", "TAT"])
        # Add test rows
        ws.append(["TEST1", "Test One", "Hematology", "Blood", 100.00, 24])
        ws.append(["TEST2", "Test Two", "Chemistry", "Serum", 200.00, 48])
        
        # Save to BytesIO
        file_obj = BytesIO()
        wb.save(file_obj)
        file_obj.seek(0)
        
        # Import
        summary = import_tests_from_excel(file_obj)
        
        # Check summary
        assert summary["tests_created"] == 2
        assert Test.objects.filter(test_code="TEST1").exists()
        assert Test.objects.filter(test_code="TEST2").exists()
        
        # Check categories were created
        assert TestCategory.objects.filter(name="Hematology").exists()
        assert TestCategory.objects.filter(name="Chemistry").exists()
    
    def test_import_parameters_sheet(self):
        """Test importing parameters from Excel Parameters sheet."""
        # Create test first
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="TEST1",
            test_name="Test One",
            sample_type="Blood",
            price=Decimal("100.00"),
            turnaround_time=24,
        )
        
        # Create workbook with Parameters sheet
        wb = Workbook()
        ws = wb.create_sheet("Parameters")
        
        # Add header row
        ws.append(["TestCode", "Name", "Unit", "Order", "DecimalPlaces"])
        # Add parameter rows
        ws.append(["TEST1", "Param1", "g/dL", 1, 2])
        ws.append(["TEST1", "Param2", "mg/dL", 2, 1])
        
        # Save to BytesIO
        file_obj = BytesIO()
        wb.save(file_obj)
        file_obj.seek(0)
        
        # Import
        summary = import_tests_from_excel(file_obj)
        
        # Check summary
        assert summary["parameters_created"] == 2
        assert TestParameter.objects.filter(test=test, parameter_name="Param1").exists()
        assert TestParameter.objects.filter(test=test, parameter_name="Param2").exists()
    
    def test_import_reference_ranges_sheet(self):
        """Test importing reference ranges from Excel ReferenceRanges sheet."""
        # Create test and parameter first
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="TEST1",
            test_name="Test One",
            sample_type="Blood",
            price=Decimal("100.00"),
            turnaround_time=24,
        )
        param = TestParameter.objects.create(
            test=test,
            parameter_name="Param1",
            unit="g/dL",
        )
        
        # Create workbook with ReferenceRanges sheet
        wb = Workbook()
        ws = wb.create_sheet("ReferenceRanges")
        
        # Add header row
        ws.append(["TestCode", "ParameterName", "Gender", "AgeMin", "AgeMax", "Min", "Max", "CritLow", "CritHigh"])
        # Add range row
        ws.append(["TEST1", "Param1", "Male", 18, 65, 10.0, 20.0, 5.0, 25.0])
        
        # Save to BytesIO
        file_obj = BytesIO()
        wb.save(file_obj)
        file_obj.seek(0)
        
        # Import
        summary = import_tests_from_excel(file_obj)
        
        # Check summary
        assert summary["ranges_created"] == 1
        assert ReferenceRange.objects.filter(
            parameter=param,
            gender="Male",
            age_min=18,
            age_max=65,
        ).exists()
    
    def test_import_all_sheets_together(self):
        """Test importing all sheets together."""
        wb = Workbook()
        
        # Tests sheet
        ws_tests = wb.create_sheet("Tests")
        ws_tests.append(["Code", "Name", "Category", "SampleType", "Price", "TAT"])
        ws_tests.append(["TEST1", "Test One", "Hematology", "Blood", 100.00, 24])
        
        # Parameters sheet
        ws_params = wb.create_sheet("Parameters")
        ws_params.append(["TestCode", "Name", "Unit", "Order", "DecimalPlaces"])
        ws_params.append(["TEST1", "Param1", "g/dL", 1, 2])
        
        # ReferenceRanges sheet
        ws_ranges = wb.create_sheet("ReferenceRanges")
        ws_ranges.append(["TestCode", "ParameterName", "Gender", "AgeMin", "AgeMax", "Min", "Max", "CritLow", "CritHigh"])
        ws_ranges.append(["TEST1", "Param1", "Male", 18, 65, 10.0, 20.0, 5.0, 25.0])
        
        # Save to BytesIO
        file_obj = BytesIO()
        wb.save(file_obj)
        file_obj.seek(0)
        
        # Import
        summary = import_tests_from_excel(file_obj)
        
        # Check all data imported
        assert summary["tests_created"] == 1
        assert summary["parameters_created"] == 1
        assert summary["ranges_created"] == 1
        
        test = Test.objects.get(test_code="TEST1")
        param = TestParameter.objects.get(test=test, parameter_name="Param1")
        assert ReferenceRange.objects.filter(parameter=param).exists()
    
    def test_import_updates_existing_test(self):
        """Test that import updates existing test instead of creating duplicate."""
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="TEST1",
            test_name="Old Name",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=12,
        )
        
        # Create workbook with updated test data
        wb = Workbook()
        ws = wb.create_sheet("Tests")
        ws.append(["Code", "Name", "Category", "SampleType", "Price", "TAT"])
        ws.append(["TEST1", "New Name", "Hematology", "Serum", 100.00, 24])
        
        file_obj = BytesIO()
        wb.save(file_obj)
        file_obj.seek(0)
        
        # Import
        summary = import_tests_from_excel(file_obj)
        
        # Check test was updated, not created
        assert summary["tests_updated"] == 1
        assert summary["tests_created"] == 0
        
        test.refresh_from_db()
        assert test.test_name == "New Name"
        assert test.sample_type == "Serum"
    
    def test_import_skips_empty_rows(self):
        """Test that import skips empty rows."""
        wb = Workbook()
        ws = wb.create_sheet("Tests")
        ws.append(["Code", "Name", "Category", "SampleType", "Price", "TAT"])
        ws.append(["TEST1", "Test One", "Hematology", "Blood", 100.00, 24])
        ws.append([None, None, None, None, None, None])  # Empty row
        ws.append(["TEST2", "Test Two", "Chemistry", "Serum", 200.00, 48])
        
        file_obj = BytesIO()
        wb.save(file_obj)
        file_obj.seek(0)
        
        # Import
        summary = import_tests_from_excel(file_obj)
        
        # Should only create 2 tests, skipping empty row
        assert summary["tests_created"] == 2
    
    def test_import_handles_missing_test_for_parameter(self):
        """Test that import handles missing test gracefully for parameters."""
        wb = Workbook()
        ws = wb.create_sheet("Parameters")
        ws.append(["TestCode", "Name", "Unit", "Order", "DecimalPlaces"])
        ws.append(["NONEXISTENT", "Param1", "g/dL", 1, 2])
        
        file_obj = BytesIO()
        wb.save(file_obj)
        file_obj.seek(0)
        
        # Import should not raise error
        summary = import_tests_from_excel(file_obj)
        
        # No parameters should be created
        assert summary["parameters_created"] == 0
    
    def test_import_handles_missing_parameter_for_range(self):
        """Test that import handles missing parameter gracefully for ranges."""
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="TEST1",
            test_name="Test One",
            sample_type="Blood",
            price=Decimal("100.00"),
            turnaround_time=24,
        )
        
        wb = Workbook()
        ws = wb.create_sheet("ReferenceRanges")
        ws.append(["TestCode", "ParameterName", "Gender", "AgeMin", "AgeMax", "Min", "Max", "CritLow", "CritHigh"])
        ws.append(["TEST1", "NONEXISTENT", "Male", 18, 65, 10.0, 20.0, 5.0, 25.0])
        
        file_obj = BytesIO()
        wb.save(file_obj)
        file_obj.seek(0)
        
        # Import should not raise error
        summary = import_tests_from_excel(file_obj)
        
        # No ranges should be created
        assert summary["ranges_created"] == 0


