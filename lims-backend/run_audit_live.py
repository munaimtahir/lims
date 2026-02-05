
import os
import django
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.laboratory.models import Test, Parameter, TestParameter, ReferenceRange, TestPanel
from django.db.models import Count, Q, F

def run_audit():
    print("Running Audit on EXISTING Database...")
    
    duplicate_test_codes = (
        Test.objects.values("test_code")
        .annotate(count=Count("test_id"))
        .filter(count__gt=1)
    )
    duplicate_param_codes = (
        Parameter.objects.values("parameter_id")
        .annotate(count=Count("parameter_id"))
        .filter(count__gt=1)
    )
    tests_without_parameters = (
        Test.objects.filter(test_parameters__isnull=True)
        .values("test_id", "test_code", "test_name")[:10]
    )
    orphan_mappings = (
        TestParameter.objects.filter(
            Q(test__isnull=True) | Q(parameter__isnull=True)
        )
    )
    missing_ranges = (
        TestParameter.objects.filter(reference_ranges__isnull=True)
        .values("test_id", "parameter_id")[:10]
    )
    invalid_ranges = (
        ReferenceRange.objects.filter(
            Q(reference_min__isnull=True, reference_max__isnull=True)
            | Q(age_min__gte=F("age_max"))
        )
    )
    serum_defaults = Test.objects.filter(sample_type__iexact="Serum")
    zero_price = Test.objects.filter(price=0)
    default_tat = Test.objects.filter(turnaround_time=24)
    panels_without_tests = TestPanel.objects.filter(tests__isnull=True)

    results = {
        "duplicates": {
            "test_code": {
                "count": duplicate_test_codes.count(),
                "samples": list(duplicate_test_codes[:10]),
            },
            "parameter_code": {
                "count": duplicate_param_codes.count(),
                "samples": list(duplicate_param_codes[:10]),
            },
        },
        "orphans": {
            "mappings": {
                "count": orphan_mappings.count(),
                "samples": list(orphan_mappings.values("id", "test_id", "parameter_id")[:10]),
            },
        },
        "tests_without_parameters": {
            "count": Test.objects.filter(test_parameters__isnull=True).count(),
            "samples": list(tests_without_parameters),
        },
        "reference_ranges": {
            "missing": {
                "count": TestParameter.objects.filter(reference_ranges__isnull=True).count(),
                # Note: 'parameter_id' in values() refers to the ForeignKey id (string p-code), 
                # but depending on Django version/setup, checking simple access is safer.
                "samples": list(missing_ranges),
            },
            "invalid": {
                "count": invalid_ranges.count(),
                "samples": list(invalid_ranges.values("id", "parameter_id", "gender")[:10]),
            },
        },
        "suspicious_defaults": {
            "sample_type_serum": {
                "count": serum_defaults.count(),
                "samples": list(serum_defaults.values("test_id", "test_code")[:10]),
            },
            "price_zero": {
                "count": zero_price.count(),
                "samples": list(zero_price.values("test_id", "test_code")[:10]),
            },
            "turnaround_time_24": {
                "count": default_tat.count(),
                "samples": list(default_tat.values("test_id", "test_code")[:10]),
            },
        },
        "panels_without_tests": {
            "count": panels_without_tests.count(),
            "samples": list(panels_without_tests.values("panel_code", "panel_name")[:10]),
        },
    }
    
    print(json.dumps(results, indent=2, default=str))

if __name__ == "__main__":
    run_audit()
