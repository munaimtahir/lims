from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.laboratory.ranges import pick_reference_range
from apps.results.models import TestResult


def _get_panel_tests(panel):
    return list(panel.tests.all().order_by("test_name", "id"))


def get_orderitem_expected_parameters(order_item, patient) -> list[dict[str, Any]]:
    expected: list[dict[str, Any]] = []

    tests = []
    if order_item.test:
        tests = [order_item.test]
    elif order_item.panel:
        tests = _get_panel_tests(order_item.panel)

    for test in tests:
        parameters = test.test_parameters.all().order_by("display_order", "id")
        for parameter in parameters:
            range_info = pick_reference_range(parameter, patient)
            expected.append(
                {
                    "test_id": test.test_id,
                    "test_name": test.test_name,
                    "parameter_id": parameter.id,
                    "parameter_name": parameter.effective_parameter_name,
                    "unit": parameter.unit,
                    "display_order": parameter.display_order,
                    "reference_display": range_info["display"],
                }
            )
    return expected


@transaction.atomic
def ensure_test_results(order_item) -> list[TestResult]:
    """
    Ensure test result rows exist for an order item.

    Uses transaction.atomic() to prevent race conditions and ensure
    consistency when multiple requests process the same order_item concurrently.

    Args:
        order_item: The OrderItem to create results for

    Returns:
        List of TestResult instances (created or existing)
    """
    patient = getattr(order_item.order, "patient", None)
    expected = get_orderitem_expected_parameters(order_item, patient)
    results = []
    for item in expected:
        result, _created = TestResult.objects.get_or_create(
            order_item=order_item,
            test_parameter_id=item["parameter_id"],
            defaults={"result_value": "", "status": "DRAFT"},
        )
        results.append(result)
    return results
