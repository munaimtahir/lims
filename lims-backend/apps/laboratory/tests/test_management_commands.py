"""
Tests for management commands.
"""
import pytest
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from apps.laboratory.models import TestCategory, Test, TestParameter, TestPanel


@pytest.mark.django_db
class TestSeedTestCatalogCommand:
    """Test seed_test_catalog management command."""
    
    def test_seed_command_creates_data(self):
        """Test that seed command creates categories, tests, parameters, and panels."""
        # Initially empty
        assert TestCategory.objects.count() == 0
        assert Test.objects.count() == 0
        assert TestParameter.objects.count() == 0
        assert TestPanel.objects.count() == 0
        
        # Run command
        out = StringIO()
        call_command('seed_test_catalog', stdout=out)
        
        # Check data was created
        assert TestCategory.objects.count() > 0
        assert Test.objects.count() > 0
        assert TestParameter.objects.count() > 0
        assert TestPanel.objects.count() > 0
        
        # Check specific categories exist
        assert TestCategory.objects.filter(name="Hematology").exists()
        assert TestCategory.objects.filter(name="Clinical Chemistry").exists()
        
        # Check specific tests exist
        assert Test.objects.filter(test_code="CBC").exists()
        assert Test.objects.filter(test_code="GLUCOSE").exists()
        
        # Check panels exist
        assert TestPanel.objects.filter(panel_code="LFT").exists()
        assert TestPanel.objects.filter(panel_code="RFT").exists()
    
    def test_seed_command_idempotent(self):
        """Test that seed command is idempotent (can run multiple times)."""
        # Run command first time
        out1 = StringIO()
        call_command('seed_test_catalog', stdout=out1)
        count1 = {
            'categories': TestCategory.objects.count(),
            'tests': Test.objects.count(),
            'parameters': TestParameter.objects.count(),
            'panels': TestPanel.objects.count(),
        }
        
        # Run command second time
        out2 = StringIO()
        call_command('seed_test_catalog', stdout=out2)
        count2 = {
            'categories': TestCategory.objects.count(),
            'tests': Test.objects.count(),
            'parameters': TestParameter.objects.count(),
            'panels': TestPanel.objects.count(),
        }
        
        # Counts should be the same (idempotent)
        assert count1 == count2
    
    def test_seed_command_with_clear(self):
        """Test seed command with --clear option."""
        # Create some existing data
        category = TestCategory.objects.create(name="Existing Category")
        test = Test.objects.create(
            category=category,
            test_code="EXISTING",
            test_name="Existing Test",
            sample_type="Serum",
            price=100.00,
            turnaround_time=24,
        )
        
        assert TestCategory.objects.count() == 1
        assert Test.objects.count() == 1
        
        # Run command with --clear
        out = StringIO()
        call_command('seed_test_catalog', '--clear', stdout=out)
        
        # Existing data should be gone, new data created
        assert not TestCategory.objects.filter(name="Existing Category").exists()
        assert not Test.objects.filter(test_code="EXISTING").exists()
        assert TestCategory.objects.count() > 0
        assert Test.objects.count() > 0
    
    def test_seed_command_creates_categories(self):
        """Test that seed command creates all expected categories."""
        out = StringIO()
        call_command('seed_test_catalog', stdout=out)
        
        expected_categories = [
            "Hematology",
            "Clinical Chemistry",
            "Microbiology",
            "Immunology",
            "Hormones",
            "Coagulation",
            "Urinalysis",
        ]
        
        for cat_name in expected_categories:
            assert TestCategory.objects.filter(name=cat_name).exists()
    
    def test_seed_command_creates_tests_with_parameters(self):
        """Test that seed command creates tests with their parameters."""
        out = StringIO()
        call_command('seed_test_catalog', stdout=out)
        
        # Check CBC test exists with parameters
        cbc_test = Test.objects.filter(test_code="CBC").first()
        assert cbc_test is not None
        
        # Check CBC has parameters
        cbc_params = TestParameter.objects.filter(test=cbc_test)
        assert cbc_params.count() > 0
        
        # Check specific parameters exist
        assert cbc_params.filter(parameter_name="Hemoglobin").exists()
        assert cbc_params.filter(parameter_name="White Blood Cell Count").exists()
    
    def test_seed_command_creates_panels(self):
        """Test that seed command creates test panels."""
        out = StringIO()
        call_command('seed_test_catalog', stdout=out)
        
        # Check panels exist
        lft_panel = TestPanel.objects.filter(panel_code="LFT").first()
        assert lft_panel is not None
        assert lft_panel.tests.count() > 0
        
        rft_panel = TestPanel.objects.filter(panel_code="RFT").first()
        assert rft_panel is not None
        assert rft_panel.tests.count() > 0
        
        lipid_panel = TestPanel.objects.filter(panel_code="LIPID").first()
        assert lipid_panel is not None
        assert lipid_panel.tests.count() > 0


