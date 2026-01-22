import openpyxl
import re
from decimal import Decimal
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from .models import TestCategory, Test, Parameter, TestParameter, ReferenceRange, validate_parameter_id


class DummyContext:
    """Context manager for dry-run mode that doesn't create a transaction."""
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

def import_tests_from_excel(file, dry_run=False):
    """
    Import tests, parameters, and mappings from an Excel file using ID-based logic.

    Expected Sheets:
    - Tests: test_id, test_code, legacy_test_code, test_name, category, sample_type, price, turnaround_time
    - Parameters: parameter_id, parameter_name, unit
    - Mapping: test_id, parameter_id, display_order, reportable
    - ReferenceRanges: test_id, parameter_id, gender, age_min, age_max, reference_min, reference_max, critical_low, critical_high
    
    Args:
        file: Excel file object
        dry_run (bool): If True, validates everything but doesn't write to DB
    
    Returns:
        dict: Summary with counts and detailed error messages
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
    
    # Track parameters and tests for validation
    parameter_ids_in_file = set()
    test_ids_in_file = set()

    def add_error(sheet, row_num, column, message, example_fix=None):
        """Helper to add structured error message."""
        error = {
            "sheet": sheet,
            "row": row_num,
            "column": column,
            "message": message
        }
        if example_fix:
            error["example_fix"] = example_fix
        summary["errors"].append(error)
        summary["validation_passed"] = False
    
    # Use transaction only if not dry run
    transaction_context = transaction.atomic() if not dry_run else DummyContext()
    
    with transaction_context:
        # 1. Import Global Parameters
        if "Parameters" in workbook.sheetnames:
            sheet = workbook["Parameters"]
            row_num = 1  # Start at 1 for header
            for row in sheet.iter_rows(min_row=2, values_only=True):
                row_num += 1
                
                # Columns: parameter_id, parameter_name, unit
                if not row[0]: 
                    continue
                
                param_id = str(row[0]).strip()
                
                # Validate parameter_id is not empty
                if not param_id:
                    add_error("Parameters", row_num, "parameter_id", 
                             "parameter_id cannot be empty")
                    continue
                
                # Validate parameter_id format
                try:
                    normalized_id = validate_parameter_id(param_id)
                except ValidationError as e:
                    add_error("Parameters", row_num, "parameter_id",
                             str(e),
                             "Use format like: p1, p2, p53")
                    continue
                
                # Check for duplicates within the file
                if normalized_id in seen_param_ids:
                    add_error("Parameters", row_num, "parameter_id",
                             f"Duplicate parameter_id in file: {param_id}",
                             "Each parameter_id must be unique")
                    continue
                
                seen_param_ids.add(normalized_id)
                parameter_ids_in_file.add(normalized_id)
                
                # Validate parameter_name is not empty
                name = row[1] if len(row) > 1 else None
                if not name:
                    add_error("Parameters", row_num, "parameter_name",
                             "parameter_name cannot be empty")
                    continue
                
                unit = row[2] if len(row) > 2 else ""

                if not dry_run:
                    try:
                        parameter, created = Parameter.objects.update_or_create(
                            parameter_id=normalized_id,
                            defaults={
                                "parameter_name": str(name).strip(),
                                "unit": str(unit).strip() if unit else "",
                                "active": True
                            }
                        )

                        if created:
                            summary["parameters_created"] += 1
                        else:
                            summary["parameters_updated"] += 1
                    except Exception as e:
                        add_error("Parameters", row_num, "parameter_id",
                                 f"Database error: {str(e)}")
                else:
                    # In dry run, just count what would happen
                    exists = Parameter.objects.filter(parameter_id=normalized_id).exists()
                    if exists:
                        summary["parameters_updated"] += 1
                    else:
                        summary["parameters_created"] += 1

        # 2. Import Tests
        if "Tests" in workbook.sheetnames:
            sheet = workbook["Tests"]
            row_num = 1
            for row in sheet.iter_rows(min_row=2, values_only=True):
                row_num += 1
                
                # Columns: test_id, test_code, legacy_test_code, test_name, category, sample_type, price, tat
                if not row[0]: 
                    continue
                
                try:
                    t_id = int(row[0])
                except (ValueError, TypeError):
                    add_error("Tests", row_num, "test_id",
                             f"test_id must be a number: {row[0]}")
                    continue
                
                if t_id in seen_test_ids:
                    add_error("Tests", row_num, "test_id",
                             f"Duplicate test_id in file: {t_id}")
                    continue
                seen_test_ids.add(t_id)
                test_ids_in_file.add(t_id)

                code, legacy_code, name, cat_name, s_type, price, tat = row[1:8]
                
                if not code:
                    add_error("Tests", row_num, "test_code",
                             "test_code cannot be empty")
                    continue
                
                if not name:
                    add_error("Tests", row_num, "test_name",
                             "test_name cannot be empty")
                    continue
                
                if not dry_run:
                    try:
                        category, _ = TestCategory.objects.get_or_create(name=cat_name or "General")

                        test, created = Test.objects.update_or_create(
                            test_id=t_id,
                            defaults={
                                "test_code": str(code).strip(),
                                "legacy_test_code": str(legacy_code).strip() if legacy_code else None,
                                "test_name": str(name).strip(),
                                "category": category,
                                "sample_type": str(s_type).strip() if s_type else "Serum",
                                "price": Decimal(str(price or 0)),
                                "turnaround_time": int(tat or 24),
                            }
                        )

                        if created:
                            summary["tests_created"] += 1
                        else:
                            summary["tests_updated"] += 1
                    except Exception as e:
                        add_error("Tests", row_num, "test_id",
                                 f"Database error: {str(e)}")
                else:
                    exists = Test.objects.filter(test_id=t_id).exists()
                    if exists:
                        summary["tests_updated"] += 1
                    else:
                        summary["tests_created"] += 1

        # 3. Import Test-Parameter Mapping
        if "Mapping" in workbook.sheetnames:
            sheet = workbook["Mapping"]
            row_num = 1
            for row in sheet.iter_rows(min_row=2, values_only=True):
                row_num += 1
                
                # Columns: test_id, parameter_id, display_order, reportable
                if not row[0] or not row[1]: 
                    continue

                t_id, p_id, order, reportable = row[:4]
                
                # Validate test_id
                try:
                    t_id = int(t_id)
                except (ValueError, TypeError):
                    add_error("Mapping", row_num, "test_id",
                             f"test_id must be a number: {t_id}")
                    continue
                
                # Normalize and validate parameter_id
                p_id_str = str(p_id).strip()
                try:
                    normalized_p_id = validate_parameter_id(p_id_str)
                except ValidationError as e:
                    add_error("Mapping", row_num, "parameter_id",
                             f"Invalid parameter_id format: {p_id_str}",
                             "Use format like: p1, p2, p53")
                    continue
                
                # Check if parameter_id was defined in Parameters sheet
                if normalized_p_id not in parameter_ids_in_file:
                    # Check if it exists in database (for existing parameters)
                    if not Parameter.objects.filter(parameter_id=normalized_p_id).exists():
                        add_error("Mapping", row_num, "parameter_id",
                                 f"Parameter {normalized_p_id} not found in Parameters sheet or database",
                                 f"Add {normalized_p_id} to the Parameters sheet first")
                        continue
                
                # Check if test_id was defined in Tests sheet or exists in DB
                if t_id not in test_ids_in_file:
                    if not Test.objects.filter(test_id=t_id).exists():
                        add_error("Mapping", row_num, "test_id",
                                 f"Test {t_id} not found in Tests sheet or database",
                                 f"Add test_id {t_id} to the Tests sheet first")
                        continue
                
                if not dry_run:
                    try:
                        test = Test.objects.get(test_id=t_id)
                        parameter = Parameter.objects.get(parameter_id=normalized_p_id)
                        
                        tp, created = TestParameter.objects.update_or_create(
                            test=test,
                            parameter=parameter,
                            defaults={
                                "display_order": int(order or 0),
                                "reportable": bool(reportable if reportable is not None else True)
                            }
                        )
                        if created:
                            summary["mappings_created"] += 1
                    except (Test.DoesNotExist, Parameter.DoesNotExist) as e:
                        add_error("Mapping", row_num, "parameter_id",
                                 f"Test {t_id} or Parameter {normalized_p_id} not found: {str(e)}")
                        continue
                    except Exception as e:
                        add_error("Mapping", row_num, "parameter_id",
                                 f"Database error: {str(e)}")
                        continue
                else:
                    # In dry run, check if mapping exists
                    try:
                        test = Test.objects.get(test_id=t_id)
                        parameter = Parameter.objects.get(parameter_id=normalized_p_id)
                        exists = TestParameter.objects.filter(test=test, parameter=parameter).exists()
                        if not exists:
                            summary["mappings_created"] += 1
                    except (Test.DoesNotExist, Parameter.DoesNotExist):
                        pass  # Already logged error above

        # 4. Import Reference Ranges
        if "ReferenceRanges" in workbook.sheetnames:
            sheet = workbook["ReferenceRanges"]
            row_num = 1
            for row in sheet.iter_rows(min_row=2, values_only=True):
                row_num += 1
                
                # Columns: test_id, parameter_id, gender, age_min, age_max, min, max, crit_low, crit_high
                if not row[0] or not row[1]: 
                    continue

                t_id, p_id, gender, amin, amax, rmin, rmax, clow, chigh = row[:9]

                # Validate test_id
                try:
                    t_id = int(t_id)
                except (ValueError, TypeError):
                    add_error("ReferenceRanges", row_num, "test_id",
                             f"test_id must be a number: {t_id}")
                    continue
                
                # Normalize and validate parameter_id
                p_id_str = str(p_id).strip()
                try:
                    normalized_p_id = validate_parameter_id(p_id_str)
                except ValidationError as e:
                    add_error("ReferenceRanges", row_num, "parameter_id",
                             f"Invalid parameter_id format: {p_id_str}",
                             "Use format like: p1, p2, p53")
                    continue

                if not dry_run:
                    try:
                        test = Test.objects.get(test_id=t_id)
                        parameter = Parameter.objects.get(parameter_id=normalized_p_id)
                        test_parameter = TestParameter.objects.get(test=test, parameter=parameter)

                        ReferenceRange.objects.update_or_create(
                            parameter=test_parameter,
                            gender=gender or "Both",
                            age_min=int(amin) if amin is not None else None,
                            age_max=int(amax) if amax is not None else None,
                            defaults={
                                "reference_min": Decimal(str(rmin)) if rmin is not None else None,
                                "reference_max": Decimal(str(rmax)) if rmax is not None else None,
                                "critical_low": Decimal(str(clow)) if clow is not None else None,
                                "critical_high": Decimal(str(chigh)) if chigh is not None else None,
                                "is_active": True,
                            }
                        )
                        summary["ranges_created"] += 1

                    except (Test.DoesNotExist, Parameter.DoesNotExist, TestParameter.DoesNotExist):
                        add_error("ReferenceRanges", row_num, "parameter_id",
                                 f"Mapping for Test {t_id} and Parameter {normalized_p_id} not found",
                                 "Ensure this test-parameter mapping exists in the Mapping sheet")
                        continue
                    except Exception as e:
                        add_error("ReferenceRanges", row_num, "parameter_id",
                                 f"Database error: {str(e)}")
                        continue
                else:
                    # In dry run, just check if mapping exists
                    try:
                        test = Test.objects.get(test_id=t_id)
                        parameter = Parameter.objects.get(parameter_id=normalized_p_id)
                        test_parameter = TestParameter.objects.get(test=test, parameter=parameter)
                        summary["ranges_created"] += 1
                    except (Test.DoesNotExist, Parameter.DoesNotExist, TestParameter.DoesNotExist):
                        add_error("ReferenceRanges", row_num, "parameter_id",
                                 f"Mapping for Test {t_id} and Parameter {normalized_p_id} not found",
                                 "Ensure this test-parameter mapping exists in the Mapping sheet")
                        continue
    
    # Add validation summary
    if summary["errors"]:
        summary["validation_passed"] = False
    
    if dry_run:
        summary["message"] = "Dry-run completed. No changes were written to the database."
        if summary["validation_passed"]:
            summary["status"] = "PASS"
        else:
            summary["status"] = "FAIL"
    
    return summary
