import openpyxl
from decimal import Decimal
from django.db import transaction, IntegrityError
from .models import TestCategory, Test, Parameter, TestParameter, ReferenceRange

def import_tests_from_excel(file):
    """
    Import tests, parameters, and mappings from an Excel file using ID-based logic.

    Expected Sheets:
    - Tests: test_id, test_code, legacy_test_code, test_name, category, sample_type, price, turnaround_time
    - Parameters: parameter_id, parameter_name, unit
    - Mapping: test_id, parameter_id, display_order, reportable
    - ReferenceRanges: test_id, parameter_id, gender, age_min, age_max, reference_min, reference_max, critical_low, critical_high
    """
    workbook = openpyxl.load_workbook(file)

    summary = {
        "tests_created": 0,
        "tests_updated": 0,
        "parameters_created": 0,
        "parameters_updated": 0,
        "mappings_created": 0,
        "ranges_created": 0,
        "errors": []
    }

    with transaction.atomic():
        # 1. Import Global Parameters
        if "Parameters" in workbook.sheetnames:
            sheet = workbook["Parameters"]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                # Columns: parameter_id, parameter_name, unit
                if not row[0]: continue
                
                param_id, name, unit = row[:3]
                param_id = str(param_id).strip()

                parameter, created = Parameter.objects.update_or_create(
                    parameter_id=param_id,
                    defaults={
                        "parameter_name": name,
                        "unit": unit or "",
                        "active": True
                    }
                )

                if created:
                    summary["parameters_created"] += 1
                else:
                    summary["parameters_updated"] += 1

        # 2. Import Tests
        if "Tests" in workbook.sheetnames:
            sheet = workbook["Tests"]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                # Columns: test_id, test_code, legacy_test_code, test_name, category, sample_type, price, tat
                if not row[0]: continue
                
                t_id, code, legacy_code, name, cat_name, s_type, price, tat = row[:8]
                
                category, _ = TestCategory.objects.get_or_create(name=cat_name or "General")

                test, created = Test.objects.update_or_create(
                    test_id=int(t_id),
                    defaults={
                        "test_code": str(code).strip(),
                        "legacy_test_code": str(legacy_code).strip() if legacy_code else None,
                        "test_name": name,
                        "category": category,
                        "sample_type": s_type or "Serum",
                        "price": Decimal(str(price or 0)),
                        "turnaround_time": int(tat or 24),
                    }
                )

                if created:
                    summary["tests_created"] += 1
                else:
                    summary["tests_updated"] += 1

        # 3. Import Test-Parameter Mapping
        if "Mapping" in workbook.sheetnames:
            sheet = workbook["Mapping"]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                # Columns: test_id, parameter_id, display_order, reportable
                if not row[0] or not row[1]: continue

                t_id, p_id, order, reportable = row[:4]
                
                try:
                    test = Test.objects.get(test_id=int(t_id))
                    parameter = Parameter.objects.get(parameter_id=str(p_id).strip())
                    
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
                    summary["errors"].append(f"Mapping error: Test {t_id} or Parameter {p_id} not found.")
                    continue

        # 4. Import Reference Ranges
        if "ReferenceRanges" in workbook.sheetnames:
            sheet = workbook["ReferenceRanges"]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                # Columns: test_id, parameter_id, gender, age_min, age_max, min, max, crit_low, crit_high
                if not row[0] or not row[1]: continue

                t_id, p_id, gender, amin, amax, rmin, rmax, clow, chigh = row[:9]

                try:
                    test = Test.objects.get(test_id=int(t_id))
                    parameter = Parameter.objects.get(parameter_id=str(p_id).strip())
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
                    summary["errors"].append(f"Range error: Mapping for Test {t_id} and Parameter {p_id} not found.")
                    continue

    return summary
