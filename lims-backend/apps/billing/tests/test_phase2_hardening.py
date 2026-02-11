import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.orders.models import Order
from apps.patients.models import Patient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def cashier(db):
    return User.objects.create_user(
        username="phase2_cashier",
        email="phase2_cashier@test.com",
        password="pass1234",
        full_name="Phase2 Cashier",
        role="Cashier",
    )


@pytest.fixture
def payment(db, cashier):
    patient = Patient.objects.create(
        first_name="Billing",
        last_name="Phase2",
        gender="Male",
        created_by=cashier,
    )
    order = Order.objects.create(patient=patient, ordered_by=cashier, total_amount=100, net_amount=100)
    response_client = APIClient()
    response_client.force_authenticate(cashier)
    response = response_client.post(
        "/api/v1/payments/",
        {"order": order.id, "amount": "100.00", "payment_method": "cash"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    from apps.billing.models import Payment

    return Payment.objects.get(pk=response.data["id"])


@pytest.mark.django_db
def test_receipt_update_blocked(api_client, cashier, payment):
    api_client.force_authenticate(cashier)
    response = api_client.patch(
        f"/api/v1/payments/{payment.id}/",
        {"notes": "edit attempt"},
        format="json",
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "detail" in response.data
