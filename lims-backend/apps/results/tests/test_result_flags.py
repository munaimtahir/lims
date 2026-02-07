from datetime import date
from decimal import Decimal

import pytest

from apps.laboratory.models import (
    Parameter,
    ReferenceRange,
    Test,
    TestCategory,
    TestParameter,
)
from apps.orders.models import Order, OrderItem
from apps.patients.models import Patient
from apps.results.models import TestResult


@pytest.fixture
def order_item(db):
    category = TestCategory.objects.create(name="Hematology")
    test = Test.objects.create(
        category=category,
        test_code="HB",
        test_name="Hemoglobin",
        sample_type="Blood",
        price=Decimal("200.00"),
        turnaround_time=2,
    )
    parameter_obj = Parameter.objects.create(
        parameter_id="p1",
        parameter_name="Hemoglobin",
        unit="g/dL",
    )
    test_parameter_obj = TestParameter.objects.create(
        test=test,
        parameter=parameter_obj,
        display_order=1,
    )
    patient = Patient.objects.create(
        first_name="Alex",
        last_name="Smith",
        date_of_birth=date(1990, 1, 1),
        gender="Male",
        phone="03001230000",
    )
    order = Order.objects.create(patient=patient, ordered_by=None, status="NEW")
    order_item = OrderItem.objects.create(order=order, test=test, price=test.price)

    ReferenceRange.objects.create(
        parameter=test_parameter_obj,
        age_min=18,
        age_max=65,
        gender="Male",
        reference_min=Decimal("13.0"),
        reference_max=Decimal("17.0"),
        critical_low=Decimal("7.0"),
        critical_high=Decimal("20.0"),
        version=1,
        is_active=True,
    )
    return order_item


@pytest.mark.django_db
def test_flag_normal(order_item):
    result = TestResult.objects.create(
        order_item=order_item,
        test_parameter=order_item.test.test_parameters.first(),
        result_value="15.0",
    )
    assert result.flag == ""


@pytest.mark.django_db
def test_flag_low(order_item):
    result = TestResult.objects.create(
        order_item=order_item,
        test_parameter=order_item.test.test_parameters.first(),
        result_value="10.0",
    )
    assert result.flag == "L"


@pytest.mark.django_db
def test_flag_high(order_item):
    result = TestResult.objects.create(
        order_item=order_item,
        test_parameter=order_item.test.test_parameters.first(),
        result_value="18.0",
    )
    assert result.flag == "H"


@pytest.mark.django_db
def test_flag_critical(order_item):
    result = TestResult.objects.create(
        order_item=order_item,
        test_parameter=order_item.test.test_parameters.first(),
        result_value="5.0",
    )
    assert result.flag == "C"
