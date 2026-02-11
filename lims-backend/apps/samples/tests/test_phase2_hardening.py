import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.laboratory.models import Test, TestCategory
from apps.orders.models import Order, OrderItem
from apps.patients.models import Patient
from apps.samples.models import Sample, SampleStatus


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def phleb(db):
    return User.objects.create_user(
        username="phase2_phleb",
        email="phase2_phleb@test.com",
        password="pass1234",
        full_name="Phase2 Admin",
        role="Admin",
    )


@pytest.fixture
def sample(db, phleb):
    patient = Patient.objects.create(
        first_name="Sample",
        last_name="Phase2",
        gender="Male",
        created_by=phleb,
    )
    category = TestCategory.objects.create(name="P2 Sample")
    test = Test.objects.create(
        category=category,
        test_code="P2S",
        test_name="Sample Test",
        sample_type="Blood",
        price=1,
        turnaround_time=1,
    )
    order = Order.objects.create(patient=patient, ordered_by=phleb)
    item = OrderItem.objects.create(order=order, test=test, price=1)
    return Sample.objects.create(order_item=item, sample_type="Blood")


@pytest.mark.django_db
def test_sample_double_collected_blocked(api_client, phleb, sample):
    api_client.force_authenticate(phleb)
    url = f"/api/v1/samples/{sample.id}/"
    first = api_client.patch(url, {"status": SampleStatus.COLLECTED}, format="json")
    assert first.status_code == status.HTTP_200_OK
    second = api_client.patch(url, {"status": SampleStatus.COLLECTED}, format="json")
    assert second.status_code == status.HTTP_409_CONFLICT
