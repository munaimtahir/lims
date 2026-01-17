from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.laboratory.models import Test, TestCategory, TestPanel, TestParameter
from apps.orders.models import Order, OrderItem
from apps.patients.models import Patient
from apps.results.models import TestResult


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin",
        email="admin@test.com",
        password="adminpass123",
        full_name="Admin User",
        role="Admin",
    )


@pytest.fixture
def authenticated_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def patient(db, admin_user):
    return Patient.objects.create(
        first_name="Casey",
        last_name="Jones",
        date_of_birth=date(1990, 1, 1),
        gender="Female",
        phone="03001112222",
        created_by=admin_user,
    )


@pytest.fixture
def order(db, patient, admin_user):
    return Order.objects.create(patient=patient, ordered_by=admin_user, status="NEW")


def _create_test_with_parameters(category, code, name, parameter_names):
    test = Test.objects.create(
        category=category,
        test_code=code,
        test_name=name,
        sample_type="Blood",
        price=Decimal("100.00"),
        turnaround_time=2,
    )
    parameters = []
    for idx, param_name in enumerate(parameter_names, start=1):
        parameters.append(
            TestParameter.objects.create(
                test=test,
                parameter_name=param_name,
                unit="mg/dL",
                reference_min_female=Decimal("1.0"),
                reference_max_female=Decimal("5.0"),
                display_order=idx,
            )
        )
    return test, parameters


@pytest.mark.django_db
def test_expected_results_single_test_order(authenticated_client, order):
    category = TestCategory.objects.create(name="Chemistry")
    test, parameters = _create_test_with_parameters(
        category, "CHEM1", "Chemistry Test", ["Param A", "Param B"]
    )
    order_item = OrderItem.objects.create(order=order, test=test, price=test.price)

    response = authenticated_client.get(
        "/api/v1/results/expected/", {"order_item_id": order_item.id}
    )

    assert response.status_code == 200
    results = response.data["results"]
    assert [row["parameter_id"] for row in results] == [p.id for p in parameters]


@pytest.mark.django_db
def test_expected_results_panel_order(authenticated_client, order):
    category = TestCategory.objects.create(name="Panels")
    alpha_test, alpha_params = _create_test_with_parameters(
        category, "A1", "Alpha Test", ["Alpha Param"]
    )
    beta_test, beta_params = _create_test_with_parameters(
        category, "B1", "Beta Test", ["Beta Param"]
    )
    panel = TestPanel.objects.create(
        panel_code="PANEL",
        panel_name="Panel One",
        category=category,
        sample_type="Blood",
        price=Decimal("200.00"),
        turnaround_time=4,
    )
    panel.tests.add(beta_test, alpha_test)

    order_item = OrderItem.objects.create(order=order, panel=panel, price=panel.price)

    response = authenticated_client.get(
        "/api/v1/results/expected/", {"order_item_id": order_item.id}
    )

    assert response.status_code == 200
    results = response.data["results"]
    expected_ids = [alpha_params[0].id, beta_params[0].id]
    assert [row["parameter_id"] for row in results] == expected_ids


@pytest.mark.django_db
def test_ensure_endpoint_idempotent(authenticated_client, order):
    category = TestCategory.objects.create(name="Immunology")
    test, parameters = _create_test_with_parameters(
        category, "IMM1", "Immuno Test", ["Param A"]
    )
    order_item = OrderItem.objects.create(order=order, test=test, price=test.price)

    response = authenticated_client.post(
        f"/api/v1/results/ensure/?order_item_id={order_item.id}"
    )
    assert response.status_code == 200
    assert TestResult.objects.filter(order_item=order_item).count() == len(parameters)

    response = authenticated_client.post(
        f"/api/v1/results/ensure/?order_item_id={order_item.id}"
    )
    assert response.status_code == 200
    assert TestResult.objects.filter(order_item=order_item).count() == len(parameters)


@pytest.mark.django_db
def test_ensure_creates_missing_rows(authenticated_client, order):
    category = TestCategory.objects.create(name="Serology")
    test, parameters = _create_test_with_parameters(
        category, "SER1", "Serology Test", ["Param A", "Param B"]
    )
    order_item = OrderItem.objects.create(order=order, test=test, price=test.price)

    response = authenticated_client.post(
        f"/api/v1/results/ensure/?order_item_id={order_item.id}"
    )

    assert response.status_code == 200
    assert TestResult.objects.filter(order_item=order_item).count() == len(parameters)
