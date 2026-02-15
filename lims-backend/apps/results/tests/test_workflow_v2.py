
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from apps.accounts.models import User
from apps.laboratory.models import Test, TestCategory, TestParameter, Parameter
from apps.orders.models import Order, OrderItem
from apps.results.models import TestResult

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin",
        email="admin@test.com",
        password="password",
        role="Admin"
    )

@pytest.fixture
def tech_user(db):
    return User.objects.create_user(
        username="tech",
        email="tech@test.com",
        password="password",
        role="Lab Technician"
    )

@pytest.fixture
def pathologist_user(db):
    user = User.objects.create_user(
        username="patho",
        email="patho@test.com",
        password="password",
        role="Pathologist"
    )
    from django.contrib.auth.models import Permission
    perm = Permission.objects.get(codename="can_verify_results")
    user.user_permissions.add(perm)
    return user

@pytest.fixture
def setup_data(db, admin_user):
    # Create Test structure
    cat = TestCategory.objects.create(name="Chem")
    test = Test.objects.create(
        category=cat, 
        test_code="POOL", 
        test_name="Pool Test", 
        price=100, 
        turnaround_time=1,
        sample_type="Serum"
    )
    
    # Param 1: Required
    p1 = Parameter.objects.create(parameter_id="p1", parameter_name="Param Required", unit="mg")
    # Added is_required=True
    tp1 = TestParameter.objects.create(test=test, parameter=p1, display_order=1, is_required=True)
    
    # Param 2: Optional
    p2 = Parameter.objects.create(parameter_id="p2", parameter_name="Param Optional", unit="mg")
    # Added is_required=False
    tp2 = TestParameter.objects.create(test=test, parameter=p2, display_order=2, is_required=False)
    
    # Patient & Order
    from apps.patients.models import Patient
    patient = Patient.objects.create(first_name="Jane", last_name="Doe", gender="Female", created_by=admin_user)
    
    order = Order.objects.create(patient=patient, ordered_by=admin_user, status="NEW")
    item = OrderItem.objects.create(order=order, test=test, price=100)
    
    return {
        "order": order,
        "item": item,
        "tp1": tp1,
        "tp2": tp2,
        "patient": patient
    }

@pytest.mark.django_db
class TestWorkflowV2:
    
    def test_draft_save_with_optional_empty(self, api_client, tech_user, setup_data):
        item = setup_data["item"]
        tp1 = setup_data["tp1"]
        tp2 = setup_data["tp2"]
        
        api_client.force_authenticate(user=tech_user)
        
        # Save valid required, leave optional empty
        payload = {
            "results": [
                {"order_item": item.id, "test_parameter": tp1.id, "result_value": "10"},
                {"order_item": item.id, "test_parameter": tp2.id, "result_value": ""}
            ]
        }
        resp = api_client.post("/api/v1/results/bulk_entry/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        
        # Verify saved state
        r1 = TestResult.objects.get(order_item=item, test_parameter=tp1)
        r2 = TestResult.objects.get(order_item=item, test_parameter=tp2)
        
        assert r1.status == "ENTERED"
        assert r1.result_value == "10"
        
        assert r2.status == "ENTERED"
        # Determine if empty string becomes * or remains empty based on implementation
        # Step 62 logic: if result_value is None or strip() == "": result_value = "*"
        assert r2.result_value == "*" 
        
        # Check Order Item Status
        item.refresh_from_db()
        assert item.status == "IN_PROCESS" 
        
        # Check Order Status
        item.order.refresh_from_db()
        assert item.order.status == "IN_PROCESS"

    def test_verify_fails_if_required_missing(self, api_client, pathologist_user, setup_data):
        item = setup_data["item"]
        tp1 = setup_data["tp1"] # Required
        
        api_client.force_authenticate(user=pathologist_user)
        
        # Create result with empty value for required param (as technician might do if bypasses UI)
        # Manually create to simulate bad data
        r1 = TestResult.objects.create(order_item=item, test_parameter=tp1, result_value="", status="ENTERED")
        
        # Try to verify
        resp = api_client.post(f"/api/v1/results/{r1.id}/verify/", format="json")
        assert resp.status_code == 400
        # The message might be "Result value required..."
        assert "required" in str(resp.data).lower()
        
    def test_verify_success_with_optional_absent(self, api_client, pathologist_user, setup_data):
        item = setup_data["item"]
        tp1 = setup_data["tp1"] # Required
        tp2 = setup_data["tp2"] # Optional
        
        api_client.force_authenticate(user=pathologist_user)
        
        # 1. Enter valid results
        r1 = TestResult.objects.create(order_item=item, test_parameter=tp1, result_value="10", status="ENTERED")
        # Optional param is absent (simulated by empty string or specific ABSENT value)
        # Using empty string
        r2 = TestResult.objects.create(order_item=item, test_parameter=tp2, result_value="", status="ENTERED") 
        
        # 2. Verify r1 (Required) -> Should Succeed
        resp = api_client.post(f"/api/v1/results/{r1.id}/verify/", format="json")
        assert resp.status_code == 200
        r1.refresh_from_db()
        assert r1.status == "VERIFIED"
        
        # 3. Verify r2 (Optional Absent) -> Should Succeed (Allowed to be absent)
        # Logic says: if optional, empty is allowed.
        resp = api_client.post(f"/api/v1/results/{r2.id}/verify/", format="json")
        assert resp.status_code == 200
        r2.refresh_from_db()
        assert r2.status == "VERIFIED"
        
        # 4. Check OrderItem Status -> Should be VERIFIED now that ALL results are verified
        item.refresh_from_db()
        assert item.status == "VERIFIED"
        
        # 5. Check Order Status -> Should be VERIFIED
        item.order.refresh_from_db()
        assert item.order.status == "VERIFIED"

    def test_unverify_flow(self, api_client, pathologist_user, setup_data):
        item = setup_data["item"]
        tp1 = setup_data["tp1"]
        
        api_client.force_authenticate(user=pathologist_user)
        
        # Setup verified result
        r1 = TestResult.objects.create(
            order_item=item, test_parameter=tp1, result_value="10", 
            status="VERIFIED", verified_by=pathologist_user, verified_at=timezone.now()
        )
        
        # Manually set order status to VERIFIED to simulate full completion
        item.status = "VERIFIED"
        item.save()
        # Bypass transition validation for test setup
        Order.objects.filter(pk=item.order.pk).update(status="VERIFIED")
        item.order.refresh_from_db()
        
        # Unverify (Reject)
        resp = api_client.post(f"/api/v1/results/{r1.id}/reject/", {"reason": "redo"}, format="json")
        assert resp.status_code == 200
        
        r1.refresh_from_db()
        assert r1.status == "ENTERED"
        assert r1.verified_by is None
        assert r1.verified_at is None
        
        # Check Item Status -> IN_PROCESS (Reversion)
        item.refresh_from_db()
        assert item.status == "IN_PROCESS"
        
        # Check Order Status -> IN_PROCESS
        item.order.refresh_from_db()
        assert item.order.status == "IN_PROCESS"

    def test_verification_queue_grouping(self, api_client, pathologist_user, setup_data):
        item = setup_data["item"]
        tp1 = setup_data["tp1"]
        
        api_client.force_authenticate(user=pathologist_user)
        
        # Create a result in ENTERED state
        TestResult.objects.create(order_item=item, test_parameter=tp1, result_value="10", status="ENTERED")
        
        resp = api_client.get("/api/v1/results/verification_queue/")
        assert resp.status_code == 200
        queue = resp.data["queue"]
        assert len(queue) == 1
        
        order_entry = queue[0]
        assert order_entry["order_id"] == item.order.order_id
        assert order_entry["items"][0]["test_name"] == item.test.test_name
