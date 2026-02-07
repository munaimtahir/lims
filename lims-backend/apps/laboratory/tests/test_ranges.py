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
from apps.laboratory.ranges import pick_reference_range
from apps.patients.models import Patient


@pytest.fixture
def test_parameter(db):
    category = TestCategory.objects.create(name="Chemistry")
    test = Test.objects.create(
        category=category,
        test_code="GLU",
        test_name="Glucose",
        sample_type="Blood",
        price=Decimal("100.00"),
        turnaround_time=2,
    )
    parameter = Parameter.objects.create(
        parameter_id="p1",
        parameter_name="Glucose",
        unit="mg/dL",
    )
    return TestParameter.objects.create(
        test=test,
        parameter=parameter,
        display_order=1,
    )


@pytest.fixture
def male_patient(db):
    return Patient.objects.create(
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 1, 1),
        gender="Male",
        phone="03001234567",
    )


@pytest.mark.django_db
def test_pick_reference_range_prefers_gender_match(test_parameter, male_patient):
    ReferenceRange.objects.create(
        parameter=test_parameter,
        age_min=0,
        age_max=120,
        gender="Both",
        reference_min=Decimal("60"),
        reference_max=Decimal("120"),
        critical_low=Decimal("40"),
        critical_high=Decimal("400"),
        version=1,
        is_active=True,
    )
    ReferenceRange.objects.create(
        parameter=test_parameter,
        age_min=18,
        age_max=65,
        gender="Male",
        reference_min=Decimal("70"),
        reference_max=Decimal("110"),
        critical_low=Decimal("45"),
        critical_high=Decimal("350"),
        version=2,
        is_active=True,
    )

    range_info = pick_reference_range(
        test_parameter, male_patient, at_date=date(2024, 1, 1)
    )

    assert range_info["source"] == "reference_range"
    assert range_info["ref_min"] == Decimal("70")
    assert range_info["ref_max"] == Decimal("110")


@pytest.mark.django_db
def test_pick_reference_range_boundary_age(test_parameter, male_patient):
    ReferenceRange.objects.create(
        parameter=test_parameter,
        age_min=18,
        age_max=30,
        gender="Male",
        reference_min=Decimal("75"),
        reference_max=Decimal("115"),
        version=1,
        is_active=True,
    )

    range_info = pick_reference_range(
        test_parameter, male_patient, at_date=date(2008, 1, 1)
    )

    assert range_info["source"] == "reference_range"
    assert range_info["ref_min"] == Decimal("75")
    assert range_info["ref_max"] == Decimal("115")


@pytest.mark.django_db
def test_pick_reference_range_missing_dob_fallback(test_parameter):
    patient = Patient.objects.create(
        first_name="Sam",
        last_name="NoDob",
        gender="Male",
        phone="03001234568",
    )
    ReferenceRange.objects.create(
        parameter=test_parameter,
        age_min=0,
        age_max=120,
        gender="Male",
        reference_min=Decimal("1"),
        reference_max=Decimal("2"),
        version=1,
        is_active=True,
    )

    range_info = pick_reference_range(test_parameter, patient)

    assert range_info["source"] == "empty"
    assert range_info["ref_min"] is None
    assert range_info["ref_max"] is None


@pytest.mark.django_db
def test_pick_reference_range_missing_ranges_returns_empty(
    test_parameter, male_patient
):
    range_info = pick_reference_range(
        test_parameter, male_patient, at_date=date(2024, 1, 1)
    )

    assert range_info["source"] == "empty"
    assert range_info["ref_min"] is None
    assert range_info["ref_max"] is None
    assert range_info["display"] == ""
