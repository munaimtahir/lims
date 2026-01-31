"""
Seed a minimal catalog if empty.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.laboratory.models import TestCategory, Test, Parameter, TestParameter, ReferenceRange


class Command(BaseCommand):
    help = "Seed a minimal CBC-style catalog if no tests exist"

    def handle(self, *args, **options):
        if Test.objects.exists():
            self.stdout.write(self.style.WARNING("Catalog already exists, skipping"))
            return 0

        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            test_id=1,
            test_code="CBC",
            test_name="Complete Blood Count",
            category=category,
            sample_type="Blood",
            price=Decimal("500.00"),
            turnaround_time=24,
        )
        hemoglobin = Parameter.objects.create(parameter_id="p1", parameter_name="Hemoglobin", unit="g/dL")
        wbc = Parameter.objects.create(parameter_id="p2", parameter_name="WBC", unit="x10^3/uL")
        mapping1 = TestParameter.objects.create(test=test, parameter=hemoglobin, display_order=1, reportable=True)
        mapping2 = TestParameter.objects.create(test=test, parameter=wbc, display_order=2, reportable=True)
        ReferenceRange.objects.create(
            parameter=mapping1,
            gender="Both",
            age_min=18,
            age_max=65,
            reference_min=Decimal("12.0"),
            reference_max=Decimal("16.0"),
            version=1,
            is_active=True,
        )
        self.stdout.write(self.style.SUCCESS("Minimal catalog seeded"))
        return 0
