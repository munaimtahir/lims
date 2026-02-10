import pytest
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth.models import Permission

from apps.accounts.models import User
from apps.laboratory.models import Test, TestCategory, TestParameter, Parameter
from apps.orders.models import Order, OrderItem
from apps.patients.models import Patient
from apps.results.models import TestResult


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        username="admin1",
        email="admin1@test.com",
        password="pass1234",
        full_name="Admin One",
        role="Admin",
    )


@pytest.fixture
def pathologist(db):
    user = User.objects.create_user(
        username="path1",
        email="path1@test.com",
        password="pass1234",
        full_name="Pathologist One",
        role="Pathologist",
    )
    perm = Permission.objects.get(codename="can_verify_results")
    user.user_permissions.add(perm)
    return user


@pytest.fixture
def patient(db, admin):
    return Patient.objects.create(
        first_name="Jane",
        last_name="Doe",
        gender="Female",
        phone="03001230000",
        created_by=admin,
    )


@pytest.fixture
def test_param(db):
    category = TestCategory.objects.create(name="Chemistry")
    test = Test.objects.create(
        category=category,
        test_code="GLU",
        test_name="Glucose",
        sample_type="Blood",
        price=10,
        turnaround_time=1,
    )
    parameter = Parameter.objects.create(parameter_id="p1", parameter_name="Glucose")
    return TestParameter.objects.create(test=test, parameter=parameter, display_order=1)


@pytest.fixture
def order(db, patient, admin, test_param):
    order = Order.objects.create(patient=patient, ordered_by=admin)
    OrderItem.objects.create(order=order, test=test_param.test, price=0)
    return order


@pytest.fixture
def draft_result(db, order, test_param, admin):
    item = order.items.first()
    return TestResult.objects.create(
        order_item=item, test_parameter=test_param, result_value="5.5", entered_by=admin
    )


@pytest.mark.django_db
def test_verify_requires_value(client, pathologist, draft_result):
    draft_result.result_value = "*"
    draft_result.save()
    client.force_authenticate(pathologist)
    response = client.post(f"/api/v1/results/{draft_result.id}/verify/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "value required" in str(response.data).lower()


@pytest.mark.django_db
def test_cannot_edit_verified_via_bulk_entry(client, pathologist, draft_result):
    client.force_authenticate(pathologist)
    # verify first
    client.post(f"/api/v1/results/{draft_result.id}/verify/")
    payload = {
        "results": [
            {
                "order_item": draft_result.order_item_id,
                "test_parameter": draft_result.test_parameter_id,
                "result_value": "9.9",
            }
        ]
    }
    response = client.post("/api/v1/results/bulk_entry/", payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot be edited" in str(response.data).lower()


@pytest.mark.django_db
def test_double_verify_returns_conflict(client, pathologist, draft_result):
    client.force_authenticate(pathologist)
    first = client.post(f"/api/v1/results/{draft_result.id}/verify/")
    assert first.status_code == status.HTTP_200_OK
    second = client.post(f"/api/v1/results/{draft_result.id}/verify/")
    assert second.status_code == status.HTTP_409_CONFLICT
