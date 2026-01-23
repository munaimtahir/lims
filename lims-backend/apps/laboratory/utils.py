"""
Utility functions for importing laboratory tests, parameters, and reference ranges from Excel.
"""
import openpyxl
from decimal import Decimal, InvalidOperation
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from .models import TestCategory, Test, Parameter, TestParameter, ReferenceRange, validate_parameter_id


class DummyContext:
    """A no-op context manager for dry-run mode to avoid actual transactions."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def get_header_map(sheet):
    """
    Extract header mappings from the first row of an Excel sheet.

    Args:
        sheet: An openpyxl worksheet object.

    Returns:
        dict: A mapping of normalized header names to column indices.
    """
    headers = {}
    if not sheet or sheet.max_row < 1:
        return headers
    for i, cell in enumerate(sheet[1]):
        if cell.value:
            h = str(cell.value).strip().lower().replace(' ', '_').replace('(', '').replace(')', '')
            headers[h] = i
    return headers


def safe_get(row, headers, keys, default=None):
    """
    Safely retrieve a cell value from a row by checking multiple possible header names.

    Args:
        row: The row tuple from iter_rows(values_only=True).
        headers: The header mapping from get_header_map.
        keys: List of possible column names to check.
        default: The value to return if no matching column is found.

    Returns:
        The cell value if found, otherwise default.
    """
    for key in keys:
        if key in headers and headers[key] < len(row):
            val = row[headers[key]]
            return val if val is not None else default
    return default


def to_decimal(val):
    """
    Convert a value to Decimal, handling None and empty strings.

    Args:
        val: The value to convert (can be str, int, float, or None).

    Returns:
        Decimal object if conversion succeeds, None otherwise.
    """
    if val is None or str(val).strip() == '':
        return None
    try:
        return Decimal(str(val).strip())
    except (InvalidOperation, ValueError):
        return None


def import_tests_from_excel(file, dry_run=False):
    """
    Import tests, parameters, test-parameter mappings, and reference ranges from Excel.

    This function processes an Excel file with up to four sheets:
    - Tests: Defines laboratory tests with columns test_id, test_code, legacy_test_code,
             test_name, category, sample_type, price, turnaround_time
    - Parameters: Defines parameters with columns parameter_id, parameter_name, unit
                 Can be a flat file with test_id column to include mappings
    - Mapping: Maps tests to parameters (test_id, parameter_id, display_order, reportable)
              Only needed if Parameters sheet doesn't include test_id column
    - ReferenceRanges: Defines normal ranges (test_id, parameter_id, gender, age_min,
                      age_max, reference_min, reference_max, critical_low, critical_high)

    Args:
        file: File-like object or path to the Excel file.
        dry_run: If True, validates data without saving to database.

    Returns:
        dict: Summary with counts of created/updated records and any validation errors.
    """
    workbook = openpyxl.load_workbook(file)
    summary = {
        "tests_created": 0,
        "tests_updated": 0,
        "parameters_created": 0,
        "parameters_updated": 0,
        "mappings_created": 0,
        "ranges_created": 0,
        "errors": [],
        "dry_run": dry_run,
        "validation_passed": True
    }

    seen_test_ids = set()
    seen_param_ids = set()
    test_ids_in_file = set()
    parameter_ids_in_file = set()

    def add_error(sheet, row_num, column, message, example_fix=None):
        error = {"sheet": sheet, "row": row_num, "column": column, "message": message}
        if example_fix:
            error["example_fix"] = example_fix
        summary["errors"].append(error)
        summary["validation_passed"] = False

    transaction_context = transaction.atomic() if not dry_run else DummyContext()

    with transaction_context:
        # 1. IMPORT TESTS
        if "Tests" in workbook.sheetnames:
            sheet = workbook["Tests"]
            headers = get_header_map(sheet)
            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
                t_id_raw = safe_get(row, headers, ['test_id', 'id'])
                if t_id_raw is None:
                    continue
                try:
                    t_id = int(t_id_raw)
                except (ValueError, TypeError):
                    add_error("Tests", row_num, "test_id", f"Invalid test ID: {t_id_raw!r}")
                    continue

                if t_id in seen_test_ids:
                    continue
                seen_test_ids.add(t_id)
                test_ids_in_file.add(t_id)

                code = str(safe_get(row, headers, ['test_code', 'code'], '')).strip()
                name = str(safe_get(row, headers, ['test_name', 'name'], '')).strip()
                legacy_code = str(safe_get(row, headers, ['legacy_test_code', 'legacy_code'], '')).strip() or None
                cat_name = str(safe_get(row, headers, ['category', 'department', 'cat'], 'General')).strip()
                s_type = str(safe_get(row, headers, ['sample_type', 'specimen'], 'Serum')).strip()
                price = to_decimal(safe_get(row, headers, ['price', 'cost'], 0))
                tat = safe_get(row, headers, ['turnaround_time', 'tat', 'tat_hours'], 24)

                if not code or not name:
                    add_error("Tests", row_num, "test_code", "Missing code or name")
                    continue

                if not dry_run:
                    category, _ = TestCategory.objects.get_or_create(name=cat_name)
                    test, created = Test.objects.update_or_create(
                        test_id=t_id,
                        defaults={
                            "test_code": code,
                            "test_name": name,
                            "legacy_test_code": legacy_code,
                            "category": category,
                            "sample_type": s_type,
                            "price": price or Decimal('0'),
                            "turnaround_time": int(tat or 24)
                        }
                    )
                    if created:
                        summary["tests_created"] += 1
                    else:
                        summary["tests_updated"] += 1
                else:
                    if Test.objects.filter(test_id=t_id).exists():
                        summary["tests_updated"] += 1
                    else:
                        summary["tests_created"] += 1

        # 2. IMPORT PARAMETERS & MAPPINGS from "Parameters" or "ParameterMaster"
        # The user's file has a "Parameters" sheet that is a flat mapping
        if "Parameters" in workbook.sheetnames:
            sheet = workbook["Parameters"]
            headers = get_header_map(sheet)
            is_flat = 'test_id' in headers

            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
                p_id_raw = safe_get(row, headers, ['parameter_id', 'param_id', 'id'])
                if not p_id_raw:
                    continue

                p_id_str = str(p_id_raw).strip()
                if p_id_str.isdigit():
                    p_id_str = f"p{p_id_str}"

                try:
                    p_id = validate_parameter_id(p_id_str)
                except ValidationError:
                    add_error(
                        "Parameters",
                        row_num,
                        "parameter_id",
                        f"Invalid parameter ID: {p_id_raw!r}",
                        "Use format like: p1, p2, p53"
                    )
                    continue

                # Create Parameter if new
                if p_id not in seen_param_ids:
                    p_name = str(safe_get(row, headers, ['parameter_name', 'name', 'analyte'], p_id)).strip()
                    unit = str(safe_get(row, headers, ['unit', 'units'], '')).strip()
                    if not dry_run:
                        param, created = Parameter.objects.update_or_create(
                            parameter_id=p_id,
                            defaults={"parameter_name": p_name, "unit": unit, "active": True}
                        )
                        if created:
                            summary["parameters_created"] += 1
                        else:
                            summary["parameters_updated"] += 1
                    else:
                        if not Parameter.objects.filter(parameter_id=p_id).exists():
                            summary["parameters_created"] += 1
                        else:
                            summary["parameters_updated"] += 1
                    seen_param_ids.add(p_id)
                    parameter_ids_in_file.add(p_id)

                # Handle Mapping if flat
                if is_flat:
                    t_id_raw = safe_get(row, headers, ['test_id'])
                    if t_id_raw:
                        try:
                            t_id = int(t_id_raw)
                            if not dry_run:
                                test = Test.objects.get(test_id=t_id)
                                param = Parameter.objects.get(parameter_id=p_id)
                                order = int(safe_get(row, headers, ['display_order', 'order'], 0) or 0)
                                tp, created = TestParameter.objects.update_or_create(
                                    test=test,
                                    parameter=param,
                                    defaults={"display_order": order, "reportable": True}
                                )
                                if created:
                                    summary["mappings_created"] += 1

                                # Ranges in flat file
                                rm_min = to_decimal(safe_get(row, headers, ['ref_min_male', 'min_male']))
                                rm_max = to_decimal(safe_get(row, headers, ['ref_max_male', 'max_male']))
                                rf_min = to_decimal(safe_get(row, headers, ['ref_min_female', 'min_female']))
                                rf_max = to_decimal(safe_get(row, headers, ['ref_max_female', 'max_female']))

                                if rm_min is not None or rm_max is not None:
                                    ReferenceRange.objects.update_or_create(
                                        parameter=tp,
                                        gender="Male",
                                        defaults={"reference_min": rm_min, "reference_max": rm_max, "is_active": True}
                                    )
                                    summary["ranges_created"] += 1
                                if rf_min is not None or rf_max is not None:
                                    ReferenceRange.objects.update_or_create(
                                        parameter=tp,
                                        gender="Female",
                                        defaults={"reference_min": rf_min, "reference_max": rf_max, "is_active": True}
                                    )
                                    summary["ranges_created"] += 1
                            else:
                                summary["mappings_created"] += 1
                                if safe_get(row, headers, ['ref_min_male']):
                                    summary["ranges_created"] += 1
                                if safe_get(row, headers, ['ref_min_female']):
                                    summary["ranges_created"] += 1
                        except (Test.DoesNotExist, Parameter.DoesNotExist, IntegrityError,
                                ValidationError, ValueError, TypeError) as e:
                            # Record structured error so users can correct problematic mappings
                            summary.setdefault("errors", []).append({
                                "sheet": "Parameters",
                                "row": row_num,
                                "test_id": t_id_raw,
                                "parameter_id": p_id,
                                "error": str(e),
                                "error_type": e.__class__.__name__,
                            })
                        except Exception as e:
                            # Catch-all to avoid breaking the entire import, but still surface the issue
                            summary.setdefault("errors", []).append({
                                "sheet": "Parameters",
                                "row": row_num,
                                "test_id": t_id_raw,
                                "parameter_id": p_id,
                                "error": str(e),
                                "error_type": e.__class__.__name__,
                            })

        # 3. IMPORT MAPPING (Explicit)
        if "Mapping" in workbook.sheetnames and (
            "Parameters" not in workbook.sheetnames or 'test_id' not in get_header_map(workbook["Parameters"])
        ):
            # Only process if Parameters sheet is NOT flat (i.e. global definition only)
            sheet = workbook["Mapping"]
            headers = get_header_map(sheet)
            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
                t_id_raw = safe_get(row, headers, ['test_id'])
                p_id_raw = safe_get(row, headers, ['parameter_id', 'param_id'])

                if not t_id_raw or not p_id_raw:
                    continue

                try:
                    t_id = int(t_id_raw)
                    p_id_str = str(p_id_raw).strip()
                    # Accept plain numeric IDs by prefixing with "p", consistent with ReferenceRanges handling
                    if p_id_str.isdigit():
                        p_id_str = f"p{p_id_str}"
                    p_id = validate_parameter_id(p_id_str)
                except (ValueError, TypeError, ValidationError):
                    # Skip rows with invalid IDs
                    continue

                if not dry_run:
                    try:
                        test = Test.objects.get(test_id=t_id)
                        param = Parameter.objects.get(parameter_id=p_id)
                        order = int(safe_get(row, headers, ['display_order', 'order'], 0) or 0)
                        reportable = safe_get(row, headers, ['reportable'], True)
                        if str(reportable).lower() in ['false', '0', 'no']:
                            reportable = False
                        else:
                            reportable = True

                        tp, created = TestParameter.objects.update_or_create(
                            test=test,
                            parameter=param,
                            defaults={"display_order": order, "reportable": reportable}
                        )
                        if created:
                            summary["mappings_created"] += 1
                    except (Test.DoesNotExist, Parameter.DoesNotExist):
                        add_error(
                            "Mapping",
                            row_num,
                            "test_id/parameter_id",
                            f"Test {t_id} or Parameter {p_id} not found",
                            "Ensure tests and parameters are defined first"
                        )
                    except (IntegrityError, ValidationError) as e:
                        add_error("Mapping", row_num, "mapping", str(e))
                else:
                    summary["mappings_created"] += 1

        # 4. IMPORT REFERENCE RANGES (Explicit)
        if "ReferenceRanges" in workbook.sheetnames:
            sheet = workbook["ReferenceRanges"]
            headers = get_header_map(sheet)
            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
                t_id_raw = safe_get(row, headers, ['test_id'])
                p_id_raw = safe_get(row, headers, ['parameter_id', 'param_id'])
                if not t_id_raw or not p_id_raw:
                    continue

                try:
                    t_id = int(t_id_raw)
                    p_id_str = str(p_id_raw).strip()
                    if p_id_str.isdigit():
                        p_id_str = f"p{p_id_str}"
                    p_id = validate_parameter_id(p_id_str)
                except (ValueError, TypeError, ValidationError):
                    continue

                gender = str(safe_get(row, headers, ['gender'], 'Both')).strip()
                a_min = safe_get(row, headers, ['age_min_years', 'age_min'], 0)
                a_max = safe_get(row, headers, ['age_max_years', 'age_max'], 999)
                r_min = to_decimal(safe_get(row, headers, ['ref_min', 'reference_min']))
                r_max = to_decimal(safe_get(row, headers, ['ref_max', 'reference_max']))
                c_low = to_decimal(safe_get(row, headers, ['critical_low']))
                c_high = to_decimal(safe_get(row, headers, ['critical_high']))

                if not dry_run:
                    try:
                        test = Test.objects.get(test_id=t_id)
                        param = Parameter.objects.get(parameter_id=p_id)
                        tp = TestParameter.objects.get(test=test, parameter=param)
                        ReferenceRange.objects.update_or_create(
                            parameter=tp,
                            gender=gender,
                            age_min=a_min,
                            age_max=a_max,
                            defaults={
                                "reference_min": r_min,
                                "reference_max": r_max,
                                "critical_low": c_low,
                                "critical_high": c_high,
                                "is_active": True
                            }
                        )
                        summary["ranges_created"] += 1
                    except TestParameter.DoesNotExist:
                        add_error(
                            "ReferenceRanges",
                            row_num,
                            "test_id/parameter_id",
                            f"Mapping for Test {t_id} and Parameter {p_id} not found",
                            "Add the mapping in the Mapping sheet first"
                        )
                    except (Test.DoesNotExist, Parameter.DoesNotExist, IntegrityError, ValidationError) as e:
                        add_error("ReferenceRanges", row_num, "range", str(e))
                else:
                    summary["ranges_created"] += 1

    if summary["errors"]:
        summary["validation_passed"] = False
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

    # Remove the default sheet created by openpyxl so we can control sheet names.
    default_sheet = wb.active
    wb.remove(default_sheet)

    # Sheet 1: Tests
    tests_sheet = wb.create_sheet(title="Tests")
    tests_headers = [
        "Test ID",           # unique identifier for the test
        "Test Code",         # unique code for the test
        "Legacy Test Code",  # optional legacy/old code for backward compatibility
        "Name",              # human-readable test name
        "Category",          # category name (e.g., Hematology)
        "Sample Type",       # e.g., Blood, Serum
        "Price",             # test price
        "Turnaround Time",   # TAT in hours
    ]
    tests_sheet.append(tests_headers)
    tests_sheet.append([
        1,                   # Test ID
        "CBC",               # Test Code
        "001",               # Legacy Test Code
        "Complete Blood Count",  # Name
        "Hematology",       # Category
        "Blood",            # Sample Type
        100.00,             # Price
        24,                 # Turnaround Time
    ])

    # Sheet 2: Parameters
    parameters_sheet = wb.create_sheet(title="Parameters")
    parameters_headers = [
        "Parameter ID",      # unique identifier for the parameter (e.g., p1, p2)
        "Name",              # human-readable parameter name
        "Units",             # e.g., g/dL, mmol/L
    ]
    parameters_sheet.append(parameters_headers)
    parameters_sheet.append([
        "p1",                # Parameter ID
        "Hemoglobin",        # Name
        "g/dL",              # Units
    ])

    # Sheet 3: Mapping (Test-Parameter mapping)
    mapping_sheet = wb.create_sheet(title="Mapping")
    mapping_headers = [
        "Test ID",           # must match a Test ID from the Tests sheet
        "Parameter ID",      # must match a Parameter ID from the Parameters sheet
        "Display Order",     # integer ordering for display
        "Reportable",        # TRUE/FALSE
    ]
    mapping_sheet.append(mapping_headers)
    mapping_sheet.append([
        1,                   # Test ID
        "p1",                # Parameter ID
        1,                   # Display Order
        "TRUE",              # Reportable
    ])

    # Sheet 4: ReferenceRanges
    reference_sheet = wb.create_sheet(title="ReferenceRanges")
    reference_headers = [
        "Test ID",           # Test associated with the parameter
        "Parameter ID",      # Parameter for which the range applies
        "Gender",            # e.g., Male, Female, Both
        "Age Min",           # minimum age (years)
        "Age Max",           # maximum age (years)
        "Reference Min",     # lower bound of normal range
        "Reference Max",     # upper bound of normal range
        "Critical Low",      # optional critical low threshold
        "Critical High",     # optional critical high threshold
    ]
    reference_sheet.append(reference_headers)
    reference_sheet.append([
        1,                   # Test ID
        "p1",                # Parameter ID
        "Female",            # Gender
        18,                  # Age Min
        65,                  # Age Max
        12.0,                # Reference Min
        16.0,                # Reference Max
        7.0,                 # Critical Low
        20.0,                # Critical High
    ])

    return wb
