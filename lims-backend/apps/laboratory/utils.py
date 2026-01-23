import openpyxl
import re
from decimal import Decimal, InvalidOperation
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from .models import TestCategory, Test, Parameter, TestParameter, ReferenceRange, validate_parameter_id

class DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

def get_header_map(sheet):
    headers = {}
    if not sheet or sheet.max_row < 1: return headers
    for i, cell in enumerate(sheet[1]):
        if cell.value:
            h = str(cell.value).strip().lower().replace(' ', '_').replace('(', '').replace(')', '')
            headers[h] = i
    return headers

def safe_get(row, headers, keys, default=None):
    for key in keys:
        if key in headers and headers[key] < len(row):
            val = row[headers[key]]
            return val if val is not None else default
    return default

def to_decimal(val):
    if val is None or str(val).strip() == '': return None
    try:
        return Decimal(str(val).strip())
    except (InvalidOperation, ValueError):
        return None

def import_tests_from_excel(file, dry_run=False):
    workbook = openpyxl.load_workbook(file)
    summary = {
        "tests_created": 0, "tests_updated": 0,
        "parameters_created": 0, "parameters_updated": 0,
        "mappings_created": 0, "ranges_created": 0,
        "errors": [], "dry_run": dry_run, "validation_passed": True
    }

    seen_test_ids = set()
    seen_param_ids = set()
    test_ids_in_file = set()
    parameter_ids_in_file = set()

    def add_error(sheet, row_num, column, message, example_fix=None):
        error = {"sheet": sheet, "row": row_num, "column": column, "message": message}
        if example_fix: error["example_fix"] = example_fix
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
                if t_id_raw is None: continue
                try:
                    t_id = int(t_id_raw)
                except (ValueError, TypeError):
                    continue
                
                if t_id in seen_test_ids: continue
                seen_test_ids.add(t_id)
                test_ids_in_file.add(t_id)

                code = str(safe_get(row, headers, ['test_code', 'code'], '')).strip()
                name = str(safe_get(row, headers, ['test_name', 'name'], '')).strip()
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
                            "category": category,
                            "sample_type": s_type,
                            "price": price or Decimal('0'),
                            "turnaround_time": int(tat or 24)
                        }
                    )
                    if created: summary["tests_created"] += 1
                    else: summary["tests_updated"] += 1
                else:
                    if Test.objects.filter(test_id=t_id).exists(): summary["tests_updated"] += 1
                    else: summary["tests_created"] += 1

        # 2. IMPORT PARAMETERS & MAPPINGS from "Parameters" or "ParameterMaster"
        # The user's file has a "Parameters" sheet that is a flat mapping
        if "Parameters" in workbook.sheetnames:
            sheet = workbook["Parameters"]
            headers = get_header_map(sheet)
            is_flat = 'test_id' in headers
            
            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
                p_id_raw = safe_get(row, headers, ['parameter_id', 'param_id', 'id'])
                if not p_id_raw: continue
                
                p_id_str = str(p_id_raw).strip()
                if p_id_str.isdigit(): p_id_str = f"p{p_id_str}"
                
                try:
                    p_id = validate_parameter_id(p_id_str)
                except (ValueError, ValidationError):
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
                        if created: summary["parameters_created"] += 1
                        else: summary["parameters_updated"] += 1
                    else:
                        if not Parameter.objects.filter(parameter_id=p_id).exists(): summary["parameters_created"] += 1
                        else: summary["parameters_updated"] += 1
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
                                    test=test, parameter=param,
                                    defaults={"display_order": order, "reportable": True}
                                )
                                if created: summary["mappings_created"] += 1
                                
                                # Ranges in flat file
                                rm_min = to_decimal(safe_get(row, headers, ['ref_min_male', 'min_male']))
                                rm_max = to_decimal(safe_get(row, headers, ['ref_max_male', 'max_male']))
                                rf_min = to_decimal(safe_get(row, headers, ['ref_min_female', 'min_female']))
                                rf_max = to_decimal(safe_get(row, headers, ['ref_max_female', 'max_female']))
                                
                                if rm_min is not None or rm_max is not None:
                                    ReferenceRange.objects.update_or_create(
                                        parameter=tp, gender="Male",
                                        defaults={"reference_min": rm_min, "reference_max": rm_max, "is_active": True}
                                    )
                                    summary["ranges_created"] += 1
                                if rf_min is not None or rf_max is not None:
                                    ReferenceRange.objects.update_or_create(
                                        parameter=tp, gender="Female",
                                        defaults={"reference_min": rf_min, "reference_max": rf_max, "is_active": True}
                                    )
                                    summary["ranges_created"] += 1
                            else:
                                summary["mappings_created"] += 1
                                if safe_get(row, headers, ['ref_min_male']): summary["ranges_created"] += 1
                                if safe_get(row, headers, ['ref_min_female']): summary["ranges_created"] += 1
                        except Exception:
                            # Intentionally ignore errors for this row so that other rows can still be processed.
                            pass

        # 4. IMPORT REFERENCE RANGES (Explicit)
        if "ReferenceRanges" in workbook.sheetnames:
            sheet = workbook["ReferenceRanges"]
            headers = get_header_map(sheet)
            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
                t_id_raw = safe_get(row, headers, ['test_id'])
                p_id_raw = safe_get(row, headers, ['parameter_id', 'param_id'])
                if not t_id_raw or not p_id_raw: continue
                
                try:
                    t_id = int(t_id_raw)
                    p_id_str = str(p_id_raw).strip()
                    if p_id_str.isdigit(): p_id_str = f"p{p_id_str}"
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
                            parameter=tp, gender=gender, age_min=a_min, age_max=a_max,
                            defaults={
                                "reference_min": r_min,"reference_max": r_max,
                                "critical_low": c_low, "critical_high": c_high, "is_active": True
                            }
                        )
                        summary["ranges_created"] += 1
                    except (Test.DoesNotExist, Parameter.DoesNotExist, TestParameter.DoesNotExist, ValidationError, IntegrityError) as exc:
                        # Silently skip errors during reference range creation to allow other rows to process
                        pass
                else:
                    summary["ranges_created"] += 1

    if summary["errors"]: summary["validation_passed"] = False
    if dry_run:
        summary["message"] = "Dry-run verification completed."
        summary["status"] = "PASS" if summary["validation_passed"] else "FAIL"
    return summary

def generate_import_template():
    """
    Generate an Excel workbook template for importing tests, parameters,
    their mappings, and reference ranges.

    The template includes:
      - Tests sheet
      - Parameters sheet
      - TestParameters sheet
      - ReferenceRanges sheet

    Each sheet contains header rows that match the expected import format
    and a single example row to guide users.
    """
    # Create a new workbook
    workbook = openpyxl.Workbook()

    # --- Tests sheet ---
    tests_sheet = workbook.active
    tests_sheet.title = "Tests"
    tests_headers = [
        "Test ID",
        "Test Name",
        "Category Name",
        "Description",
        "Is Active",
    ]
    tests_sheet.append(tests_headers)
    # Example test row
    tests_sheet.append([
        "CBC",
        "Complete Blood Count",
        "Hematology",
        "Basic blood count panel",
        "TRUE",
    ])

    # --- Parameters sheet ---
    params_sheet = workbook.create_sheet(title="Parameters")
    params_headers = [
        "Parameter ID",
        "Parameter Name",
        "Unit",
        "Decimal Places",
        "Is Active",
    ]
    params_sheet.append(params_headers)
    # Example parameter row
    params_sheet.append([
        "WBC",
        "White Blood Cell Count",
        "x10^9/L",
        1,
        "TRUE",
    ])

    # --- TestParameters (mappings) sheet ---
    mappings_sheet = workbook.create_sheet(title="TestParameters")
    mappings_headers = [
        "Test ID",
        "Parameter ID",
        "Display Order",
        "Is Mandatory",
        "Is Active",
    ]
    mappings_sheet.append(mappings_headers)
    # Example mapping row
    mappings_sheet.append([
        "CBC",
        "WBC",
        1,
        "TRUE",
        "TRUE",
    ])

    # --- ReferenceRanges sheet ---
    ranges_sheet = workbook.create_sheet(title="ReferenceRanges")
    ranges_headers = [
        "Test ID",
        "Parameter ID",
        "Gender",
        "Age Min",
        "Age Max",
        "Reference Min",
        "Reference Max",
        "Critical Low",
        "Critical High",
    ]
    ranges_sheet.append(ranges_headers)
    # Example reference range row
    ranges_sheet.append([
        "CBC",     # Test ID
        "WBC",     # Parameter ID
        "Any",     # Gender
        18,        # Age Min
        65,        # Age Max
        4.0,       # Reference Min
        11.0,      # Reference Max
        2.0,       # Critical Low
        30.0,      # Critical High
    ])

    return workbook
