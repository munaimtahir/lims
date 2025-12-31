import openpyxl
from decimal import Decimal
from django.db import transaction
from .models import TestCategory, Test, TestParameter, ReferenceRange

def import_tests_from_excel(file):
    """
    Import tests, parameters, and reference ranges from an Excel file.

    Expected Sheets:
    - Tests: Code, Name, Category, SampleType, Price, TAT
    - Parameters: TestCode, Name, Unit, Order, DecimalPlaces
    - ReferenceRanges: TestCode, ParameterName, Gender, AgeMin, AgeMax, Min, Max, CriticalLow, CriticalHigh
    """
    workbook = openpyxl.load_workbook(file)

    summary = {
        "tests_created": 0,
        "tests_updated": 0,
        "parameters_created": 0,
        "parameters_updated": 0,
        "ranges_created": 0,
    }

    with transaction.atomic():
        # 1. Import Tests
        if "Tests" in workbook.sheetnames:
            sheet = workbook["Tests"]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                # Columns: Code, Name, Category, SampleType, Price, TAT
                if not row[0]: continue  # Skip empty rows

                code, name, category_name, sample_type, price, tat = row[:6]

                category, _ = TestCategory.objects.get_or_create(name=category_name)

                test, created = Test.objects.update_or_create(
                    test_code=code,
                    defaults={
                        "test_name": name,
                        "category": category,
                        "sample_type": sample_type or "Serum",
                        "price": Decimal(str(price or 0)),
                        "turnaround_time": int(tat or 24),
                    }
                )

                if created:
                    summary["tests_created"] += 1
                else:
                    summary["tests_updated"] += 1

        # 2. Import Parameters
        if "Parameters" in workbook.sheetnames:
            sheet = workbook["Parameters"]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                # Columns: TestCode, Name, Unit, Order, DecimalPlaces
                if not row[0]: continue

                test_code, name, unit, order, decimals = row[:5]

                try:
                    test = Test.objects.get(test_code=test_code)
                    param, created = TestParameter.objects.update_or_create(
                        test=test,
                        parameter_name=name,
                        defaults={
                            "unit": unit or "",
                            "display_order": int(order or 0),
                            "decimal_places": int(decimals or 2),
                        }
                    )

                    if created:
                        summary["parameters_created"] += 1
                    else:
                        summary["parameters_updated"] += 1

                except Test.DoesNotExist:
                    continue

        # 3. Import Reference Ranges
        if "ReferenceRanges" in workbook.sheetnames:
            sheet = workbook["ReferenceRanges"]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                # Columns: TestCode, ParameterName, Gender, AgeMin, AgeMax, Min, Max, CritLow, CritHigh
                if not row[0]: continue

                test_code, param_name, gender, age_min, age_max, ref_min, ref_max, crit_low, crit_high = row[:9]

                try:
                    test = Test.objects.get(test_code=test_code)
                    param = TestParameter.objects.get(test=test, parameter_name=param_name)

                    # Create new reference range (always create new version/instance logic simplified here)
                    # For bulk import, we might want to wipe existing for this param or just add
                    # Here we will get_or_create to avoid duplicates

                    ReferenceRange.objects.update_or_create(
                        parameter=param,
                        gender=gender or "Both",
                        age_min=int(age_min) if age_min is not None else None,
                        age_max=int(age_max) if age_max is not None else None,
                        defaults={
                            "reference_min": Decimal(str(ref_min)) if ref_min is not None else None,
                            "reference_max": Decimal(str(ref_max)) if ref_max is not None else None,
                            "critical_low": Decimal(str(crit_low)) if crit_low is not None else None,
                            "critical_high": Decimal(str(crit_high)) if crit_high is not None else None,
                            "is_active": True,
                        }
                    )
                    summary["ranges_created"] += 1

                except (Test.DoesNotExist, TestParameter.DoesNotExist):
                    continue

    return summary
