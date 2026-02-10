import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.orders.models import Order, OrderItem
from apps.laboratory.models import Test, TestCategory
from apps.patients.models import Patient
from apps.samples.models import Sample, SampleStatus


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        username="admin2",
        email="admin2@test.com",
        password="pass1234",
        full_name="Admin Two",
        role="Admin",
    )


@pytest.fixture
def phleb(db):
    return User.objects.create_user(
        username="phleb",
        email="phleb@test.com",
        password="pass1234",
        full_name="Phleb One",
        role="Phlebotomist",
    )


@pytest.fixture
def labtech(db):
    return User.objects.create_user(
        username="tech",
        email="tech@test.com",
        password="pass1234",
        full_name="Tech One",
        role="Lab Technician",
    )


@pytest.fixture
def sample(db, admin):
    patient = Patient.objects.create(
        first_name="Patient",
        last_name="Sample",
        gender="Male",
        created_by=admin,
    )
    category = TestCategory.objects.create(name="Heme")
    test = Test.objects.create(
        category=category, test_code="CBC", test_name="CBC", price=0, turnaround_time=1
    )
    order = Order.objects.create(patient=patient, ordered_by=admin)
    item = OrderItem.objects.create(order=order, test=test, price=0)
    return Sample.objects.create(order_item=item, sample_type="Blood")


@pytest.mark.django_db
def test_mark_collected_idempotent(client, phleb, sample):
    client.force_authenticate(phleb)
    url = f"/api/v1/samples/{sample.id}/"
    resp1 = client.patch(url, {"status": SampleStatus.COLLECTED}, format="json")
    assert resp1.status_code == status.HTTP_200_OK
    collected_at = resp1.data.get("collected_at")
    resp2 = client.patch(url, {"status": SampleStatus.COLLECTED}, format="json")
    assert resp2.status_code == status.HTTP_200_OK
    assert resp2.data.get("collected_at") == collected_at


@pytest.mark.django_db
def test_non_manager_cannot_modify_collected(client, phleb, sample):
    client.force_authenticate(phleb)
    url = f"/api/v1/samples/{sample.id}/"
    client.patch(url, {"status": SampleStatus.COLLECTED}, format="json")
    resp = client.patch(url, {"status": SampleStatus.POSTPONED}, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_labtech_can_mark_received(client, labtech, sample):
    client.force_authenticate(labtech)
    url = f"/api/v1/samples/{sample.id}/"
    client.patch(url, {"status": SampleStatus.COLLECTED}, format="json")
    resp = client.patch(url, {"status": SampleStatus.RECEIVED}, format="json")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data.get("status") == SampleStatus.RECEIVED
