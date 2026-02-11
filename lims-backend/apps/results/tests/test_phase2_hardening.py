import pytest
from django.contrib.auth.models import Permission
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.laboratory.models import Parameter, Test, TestCategory, TestParameter
from apps.orders.models import Order, OrderItem
from apps.patients.models import Patient
from apps.results.models import TestResult


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def pathologist(db):
    user = User.objects.create_user(
        username="phase2_path",
        email="phase2_path@test.com",
        password="pass1234",
        full_name="Phase2 Pathologist",
        role="Pathologist",
    )
    user.user_permissions.add(Permission.objects.get(codename="can_verify_results"))
    return user


@pytest.fixture
def draft_result(db, pathologist):
    patient = Patient.objects.create(
        first_name="Phase2",
        last_name="Patient",
        gender="Female",
        created_by=pathologist,
    )
    category = TestCategory.objects.create(name="Phase2")
    test = Test.objects.create(
        category=category,
        test_code="P2T",
        test_name="Phase2 Test",
        sample_type="Blood",
        price=1,
        turnaround_time=1,
    )
    parameter = Parameter.objects.create(parameter_id="P2", parameter_name="P2 Param")
    test_param = TestParameter.objects.create(test=test, parameter=parameter, display_order=1)
    order = Order.objects.create(patient=patient, ordered_by=pathologist)
    item = OrderItem.objects.create(order=order, test=test, price=1)
    return TestResult.objects.create(
        order_item=item,
        test_parameter=test_param,
        result_value="8.1",
        entered_by=pathologist,
    )


@pytest.mark.django_db
def test_result_verify_emits_audit_event(api_client, pathologist, draft_result):
    api_client.force_authenticate(pathologist)
    response = api_client.post(f"/api/v1/results/{draft_result.id}/verify/")
    assert response.status_code == status.HTTP_200_OK
    assert AuditLog.objects.filter(
        entity_type="result",
        entity_id=str(draft_result.id),
        action="RESULT_VERIFIED",
    ).exists()


@pytest.mark.django_db
def test_result_verify_blocks_placeholder_value(api_client, pathologist, draft_result):
    draft_result.result_value = "*"
    draft_result.save()
    api_client.force_authenticate(pathologist)
    response = api_client.post(f"/api/v1/results/{draft_result.id}/verify/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "detail" in response.data


@pytest.mark.django_db
def test_result_double_verify_returns_409(api_client, pathologist, draft_result):
    api_client.force_authenticate(pathologist)
    assert api_client.post(f"/api/v1/results/{draft_result.id}/verify/").status_code == 200
    response = api_client.post(f"/api/v1/results/{draft_result.id}/verify/")
    assert response.status_code == status.HTTP_409_CONFLICT
