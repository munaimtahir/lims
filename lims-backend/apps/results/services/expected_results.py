from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.laboratory.ranges import pick_reference_range
from apps.results.models import TestResult


def _get_panel_tests(panel):
    return list(panel.tests.all().order_by("test_name", "test_id"))


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
def ensure_order_item_results(order_item) -> list[TestResult]:
    """
    Ensure test result rows exist for an order item.
    Also applies default values where result_value is NULL.

    Uses transaction.atomic() to prevent race conditions and ensure
    consistency when multiple requests process the same order_item concurrently.

    Args:
        order_item: The OrderItem to create results for

    Returns:
        List of TestResult instances (created or existing)
    """
    patient = getattr(order_item.order, "patient", None)
    
    # Prefetch test_parameters with their defaults to avoid N+1
    # We need to know which parameters are expected.
    # get_orderitem_expected_parameters already does some work but we need the TestParameter objects.
    
    tests = []
    if order_item.test:
        tests = [order_item.test]
    elif order_item.panel:
        tests = list(order_item.panel.tests.all())

    results = []
    for test in tests:
        # Use select_related to get default_value and other rule fields
        mappings = test.test_parameters.select_related("parameter").all()
        for mapping in mappings:
            result, created = TestResult.objects.get_or_create(
                order_item=order_item,
                test_parameter=mapping,
                defaults={
                    "result_value": mapping.default_value if mapping.default_value else None,
                    "status": "DRAFT",
                },
            )
            
            # If existed but was NULL, also check if we should apply default
            if not created and result.result_value is None and mapping.default_value:
                result.result_value = mapping.default_value
                result.save(update_fields=["result_value"])
            
            results.append(result)
            
    return results

# Alias for compatibility
ensure_test_results = ensure_order_item_results
