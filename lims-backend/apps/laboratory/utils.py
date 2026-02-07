"""
Catalog import/export utilities.
"""
import openpyxl

from .catalog_io import (
    CATALOG_COLUMNS,
    export_catalog_workbook,
    import_catalog_from_excel,
)


def import_tests_from_excel(file, dry_run=False):
    """
    Legacy wrapper for import_tests_from_excel to preserve existing behavior.
    """
    result = import_catalog_from_excel(
        file,
        strict=True,
        allow_defaults=False,
        mode="upsert",
        dry_run=dry_run,
    )
    errors = result.get("errors", [])
    summary = {
        "tests_created": result["counts"]["tests"]["created"],
        "tests_updated": result["counts"]["tests"]["updated"],
        "parameters_created": result["counts"]["parameters"]["created"],
        "parameters_updated": result["counts"]["parameters"]["updated"],
        "mappings_created": result["counts"]["mappings"]["created"],
        "ranges_created": result["counts"]["reference_ranges"]["created"],
        "errors": errors,
        "dry_run": dry_run,
        "validation_passed": len(errors) == 0,
    }
    if dry_run:
        summary["message"] = "Dry-run verification completed."
        summary["status"] = "PASS" if summary["validation_passed"] else "FAIL"
    return summary


def generate_import_template():
    """
    Generate an Excel workbook template for bulk importing tests, parameters,
    test-parameter mappings, and reference ranges.

    The workbook will contain four sheets:
      - Tests
      - Parameters
      - Mapping
      - ReferenceRanges

    Each sheet includes a header row and a single example row to guide users
    on the expected structure and values.

    Returns:
        openpyxl.Workbook: A workbook with four properly formatted sheets.
    """
    wb = openpyxl.Workbook()
    default_sheet = wb.active
    wb.remove(default_sheet)

    for sheet_name in [
        "Tests",
        "Parameters",
        "Mapping",
        "Panels",
        "PanelTests",
        "ReferenceRanges",
    ]:
        sheet = wb.create_sheet(title=sheet_name)
        sheet.append(CATALOG_COLUMNS[sheet_name])

    tests_sheet = wb["Tests"]
    tests_sheet.append(
        [
            1,
            "CBC",
            "001",
            "Complete Blood Count",
            "Hematology",
            "Blood",
            "",
            500.00,
            24,
            "",
            "",
            True,
        ]
    )

    params_sheet = wb["Parameters"]
    params_sheet.append(
        [
            "p1",
            "Hemoglobin",
            "g/dL",
            "Numeric",
            "Plain",
            2,
            "",
            "Both",
            False,
            True,
        ]
    )

    mapping_sheet = wb["Mapping"]
    mapping_sheet.append([1, "p1", 1, True])

    panels_sheet = wb["Panels"]
    panels_sheet.append(
        [
            "PAN-CBC",
            "CBC Panel",
            "Hematology",
            "Blood",
            "",
            800.00,
            24,
            "",
            True,
        ]
    )

    panel_tests_sheet = wb["PanelTests"]
    panel_tests_sheet.append(["PAN-CBC", 1])

    ranges_sheet = wb["ReferenceRanges"]
    ranges_sheet.append(
        [
            1,
            "p1",
            "Female",
            18,
            65,
            12.0,
            16.0,
            7.0,
            20.0,
            True,
            1,
            "",
        ]
    )

    return wb
