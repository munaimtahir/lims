import os
import django
from django.utils import timezone
from django.conf import settings
from rest_framework.test import APIRequestFactory

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from apps.results.models import TestResult
from apps.results.views import TestResultViewSet
from apps.orders.models import Order, OrderItem
from apps.laboratory.models import Test, TestParameter
from apps.patients.models import Patient

User = get_user_model()

def run_tests():
    print("Setting up test data...")
    # Create Users
    admin_user = User.objects.create_superuser('admin_test', 'admin@test.com', 'password')
    
    pathologist = User.objects.create_user('pathologist_test', 'path@test.com', 'password')
    path_group, _ = Group.objects.get_or_create(name='Pathologist')
    pathologist.groups.add(path_group) # Should have permission via migration
    
    tech = User.objects.create_user('tech_test', 'tech@test.com', 'password')
    # Tech has no special perms
    
    # Reload permissions
    pathologist = User.objects.get(pk=pathologist.pk)
    
    print(f"Pathologist perms: {pathologist.get_all_permissions()}")
    assert "results.can_verify_results" in pathologist.get_all_permissions(), "Pathologist missing permission"

    # Create Patient, Order, OrderItem
    patient = Patient.objects.create(first_name="Test", last_name="Patient", gender="M", date_of_birth="2000-01-01")
    order = Order.objects.create(patient=patient)
    test = Test.objects.create(test_name="Test A", test_code="TA")
    param = TestParameter.objects.create(test=test, parameter_name="Param 1", key="param1")
    item = OrderItem.objects.create(order=order, test=test)
    
    # Ensure result exists
    result, _ = TestResult.objects.get_or_create(order_item=item, test_parameter=param)
    result.status = "DRAFT"
    result.save()
    
    factory = APIRequestFactory()
    view = TestResultViewSet.as_view({'post': 'bulk_entry'})
    
    print("\n--- TEST 1: Tech updates DRAFT ---")
    data = {"results": [{"order_item": item.id, "test_parameter": param.id, "result_value": "10.0"}]}
    request = factory.post('/api/results/bulk_entry/', data, format='json')
    request.user = tech
    response = view(request)
    print(f"Response: {response.status_code} {response.data}")
    result.refresh_from_db()
    assert result.result_value == "10.0"
    assert result.status == "DRAFT"
    print("PASS")

    print("\n--- TEST 2: Tech tries to VERIFY (via verify action) ---")
    verify_view = TestResultViewSet.as_view({'post': 'verify'})
    request = factory.post(f'/api/results/{result.id}/verify/', {}, format='json')
    request.user = tech
    response = verify_view(request, pk=result.id)
    print(f"Response: {response.status_code} {response.data}")
    assert response.status_code == 403
    print("PASS")

    print("\n--- TEST 3: Pathologist verifes result ---")
    request = factory.post(f'/api/results/{result.id}/verify/', {}, format='json')
    request.user = pathologist
    response = verify_view(request, pk=result.id)
    print(f"Response: {response.status_code} {response.data}")
    assert response.status_code == 200
    result.refresh_from_db()
    assert result.status == "VERIFIED"
    assert result.verified_by == pathologist
    print("PASS")

    print("\n--- TEST 4: Tech edits VERIFIED result (should fail) ---")
    data = {"results": [{"order_item": item.id, "test_parameter": param.id, "result_value": "20.0"}]}
    request = factory.post('/api/results/bulk_entry/', data, format='json')
    request.user = tech
    response = view(request)
    print(f"Response: {response.status_code} {response.data}")
    # bulk_entry returns 200/201 but with errors in body usually, let's check response
    # My implementation returns 400 if validation errors exist and no success?
    # Or returns 201/400 with 'error_details'.
    # I set it to return 400 if created_results is empty.
    assert response.status_code == 400
    assert "You do not have permission" in str(response.data)
    result.refresh_from_db()
    assert result.result_value == "10.0" # Not changed
    print("PASS")

    print("\n--- TEST 5: Pathologist edits VERIFIED result (should succeed, remain VERIFIED) ---")
    data = {"results": [{"order_item": item.id, "test_parameter": param.id, "result_value": "30.0"}]}
    request = factory.post('/api/results/bulk_entry/', data, format='json')
    request.user = pathologist
    response = view(request)
    print(f"Response: {response.status_code} {response.data}")
    assert response.status_code == 201
    result.refresh_from_db()
    assert result.result_value == "30.0"
    assert result.status == "VERIFIED"
    print("PASS")

    print("\n--- TEST 6: Pathologist finalizes result ---")
    finalize_view = TestResultViewSet.as_view({'post': 'finalize'})
    request = factory.post(f'/api/results/{result.id}/finalize/', {}, format='json')
    request.user = pathologist
    response = finalize_view(request, pk=result.id)
    print(f"Response: {response.status_code} {response.data}")
    assert response.status_code == 200
    result.refresh_from_db()
    assert result.status == "FINAL"
    print("PASS")

    print("\n--- TEST 7: Pathologist edits FINAL result (should fail) ---")
    data = {"results": [{"order_item": item.id, "test_parameter": param.id, "result_value": "40.0"}]}
    request = factory.post('/api/results/bulk_entry/', data, format='json')
    request.user = pathologist
    response = view(request)
    print(f"Response: {response.status_code} {response.data}")
    assert response.status_code == 400
    assert "Finalized results cannot be edited" in str(response.data)
    result.refresh_from_db()
    assert result.result_value == "30.0"
    print("PASS")

    print("\n--- ALL TESTS PASSED ---")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
