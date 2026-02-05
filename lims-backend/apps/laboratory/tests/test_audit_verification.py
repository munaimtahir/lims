
import pytest
from apps.laboratory.models import Test, TestCategory, Parameter, TestParameter, ReferenceRange, TestPanel
from apps.laboratory.views import CatalogAuditView
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.models import User

@pytest.mark.django_db
class TestCatalogAuditReal:
    def test_audit_detects_existing_issues(self):
        """
        Verify that the audit actually inspects the existing database state
        by creating specific issues and asserting they are reported.
        """
        # Setup: Create a category
        cat = TestCategory.objects.create(name="Audit Test Category")

        # 1. Create a Test with NO parameters (should be detected)
        empty_test = Test.objects.create(
            category=cat,
            test_code="AUDIT001",
            test_name="Empty Test",
            sample_type="Serum",
            price=100,
            turnaround_time=24
        )

        # 2. Create a Duplicate Test Code (detect functionality checks existing DB)
        # However, the model might enforce unique test_code? Let's check. 
        # Usually test_code is unique. The audit view checks:
        # duplicate_test_codes = Test.objects.values("test_code").annotate(count=Count("test_id")).filter(count__gt=1)
        # If the model enforces uniqueness, we can't create a duplicate easily without bypassing validation/constraints.
        # Let's check if we can create another test with same code or if it raises IntegrityError.
        # For now, let's assume we can't easily force a duplicate if the DB enforces it, so we'll skip forcing that 
        # unless we know the constraint is missing or we bypass it.
        # Instead, let's create a Panel without tests.
        
        empty_panel = TestPanel.objects.create(
             category=cat,
             panel_code="PNL001",
             panel_name="Empty Panel",
             sample_type="Serum",
             price=500,
             turnaround_time=24
        )

        # 3. Create a parameter mapping with NO reference ranges
        range_test = Test.objects.create(
            category=cat,
            test_code="AUDIT002",
            test_name="Range Test",
            sample_type="Serum",
            price=100,
            turnaround_time=4
        )
        param = Parameter.objects.create(parameter_id="p9999", parameter_name="Range Param", unit="mg/dl")
        # This mapping has no corresponding ReferenceRange object
        tp = TestParameter.objects.create(test=range_test, parameter=param)

        # --- RUN AUDIT ---
        factory = APIRequestFactory()
        view = CatalogAuditView.as_view({'get': 'list'})
        request = factory.get('/laboratory/catalog/audit/')
        
        # Authenticate as Manager
        user = User.objects.create_user(username='audit_mgr', email='mgr@example.com', password='pwd', role='Manager')
        force_authenticate(request, user=user)
        
        response = view(request)
        
        assert response.status_code == 200
        data = response.data
        
        # --- ASSERTIONS ---
        print("\nAudit Data:", data)

        # Verify "Tests w/ No Params"
        tests_missing_params = data['tests_without_parameters']['samples']
        found_empty_test = any(t['test_code'] == 'AUDIT001' for t in tests_missing_params)
        assert found_empty_test, "Audit failed to detect existing test without parameters"

        # Verify "Panels w/ No Tests"
        panels_empty = data['panels_without_tests']['samples']
        found_empty_panel = any(p['panel_code'] == 'PNL001' for p in panels_empty)
        assert found_empty_panel, "Audit failed to detect existing panel without tests"

        # Verify "Missing Ranges"
        # The key is Reference Ranges > Missing
        missing_ranges = data['reference_ranges']['missing']['samples']
        # missing_ranges returns {test_id, parameter_id}
        found_missing_range = any(
            m['test_id'] == range_test.test_id and m['parameter_id'] == param.parameter_id 
            for m in missing_ranges
        )
        assert found_missing_range, "Audit failed to detect existing test parameter check missing reference range"

        print("\nSUCCESS: Audit correctly inspected the existing database state!")
