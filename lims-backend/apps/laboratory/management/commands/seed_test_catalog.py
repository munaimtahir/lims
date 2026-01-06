"""
Django management command to seed the test catalog with initial data.

This command creates test categories, tests, parameters, and panels.
It is idempotent - safe to run multiple times.
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.laboratory.models import (
    TestCategory,
    Test,
    TestParameter,
    TestPanel,
)


class Command(BaseCommand):
    help = "Seed the test catalog with initial data (idempotent)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing test catalog data..."))
            TestParameter.objects.all().delete()
            # Clear many-to-many relationships before deleting panels
            for panel in TestPanel.objects.all():
                panel.tests.clear()
            TestPanel.objects.all().delete()
            Test.objects.all().delete()
            TestCategory.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Seeding test catalog..."))

        # Create categories
        categories = self.create_categories()

        # Create tests and parameters
        tests_data = self.create_tests(categories)

        # Create panels
        self.create_panels(categories, tests_data)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded test catalog: "
                f"{TestCategory.objects.count()} categories, "
                f"{Test.objects.count()} tests, "
                f"{TestParameter.objects.count()} parameters, "
                f"{TestPanel.objects.count()} panels"
            )
        )

    def create_categories(self):
        """Create test categories."""
        categories_data = [
            {"name": "Hematology", "description": "Blood cell analysis and related tests"},
            {"name": "Clinical Chemistry", "description": "Biochemistry and metabolic tests"},
            {"name": "Microbiology", "description": "Bacterial and viral testing"},
            {"name": "Immunology", "description": "Immune system and antibody tests"},
            {"name": "Hormones", "description": "Endocrine and hormone analysis"},
            {"name": "Coagulation", "description": "Blood clotting studies"},
            {"name": "Urinalysis", "description": "Urine analysis and body fluids"},
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = TestCategory.objects.get_or_create(
                name=cat_data["name"],
                defaults={"description": cat_data["description"]},
            )
            categories[cat_data["name"]] = category
            if created:
                self.stdout.write(f"  Created category: {category.name}")

        return categories

    def create_tests(self, categories):
        """Create tests and their parameters."""
        tests_data = {
            # Hematology
            "CBC": {
                "category": categories["Hematology"],
                "test_code": "CBC",
                "test_name": "Complete Blood Count",
                "loinc_code": "58410-2",
                "sample_type": "EDTA Blood",
                "sample_volume": "2-3 mL",
                "price": Decimal("800.00"),
                "turnaround_time": 4,
                "parameters": [
                    {
                        "parameter_name": "Hemoglobin",
                        "loinc_code": "718-7",
                        "unit": "g/dL",
                        "reference_min_male": Decimal("13.5"),
                        "reference_max_male": Decimal("17.5"),
                        "reference_min_female": Decimal("12.0"),
                        "reference_max_female": Decimal("15.5"),
                        "critical_low": Decimal("7.0"),
                        "critical_high": Decimal("20.0"),
                        "decimal_places": 1,
                        "display_order": 1,
                    },
                    {
                        "parameter_name": "Hematocrit",
                        "loinc_code": "4544-3",
                        "unit": "%",
                        "reference_min_male": Decimal("40.0"),
                        "reference_max_male": Decimal("50.0"),
                        "reference_min_female": Decimal("36.0"),
                        "reference_max_female": Decimal("46.0"),
                        "critical_low": Decimal("20.0"),
                        "critical_high": Decimal("60.0"),
                        "decimal_places": 1,
                        "display_order": 2,
                    },
                    {
                        "parameter_name": "White Blood Cell Count",
                        "loinc_code": "6690-2",
                        "unit": "×10³/μL",
                        "reference_min_male": Decimal("4.0"),
                        "reference_max_male": Decimal("11.0"),
                        "reference_min_female": Decimal("4.0"),
                        "reference_max_female": Decimal("11.0"),
                        "critical_low": Decimal("2.0"),
                        "critical_high": Decimal("30.0"),
                        "decimal_places": 2,
                        "display_order": 3,
                    },
                    {
                        "parameter_name": "Platelet Count",
                        "loinc_code": "777-3",
                        "unit": "×10³/μL",
                        "reference_min_male": Decimal("150.0"),
                        "reference_max_male": Decimal("450.0"),
                        "reference_min_female": Decimal("150.0"),
                        "reference_max_female": Decimal("450.0"),
                        "critical_low": Decimal("50.0"),
                        "critical_high": Decimal("1000.0"),
                        "decimal_places": 0,
                        "display_order": 4,
                    },
                    {
                        "parameter_name": "Red Blood Cell Count",
                        "loinc_code": "789-8",
                        "unit": "×10⁶/μL",
                        "reference_min_male": Decimal("4.5"),
                        "reference_max_male": Decimal("5.5"),
                        "reference_min_female": Decimal("4.0"),
                        "reference_max_female": Decimal("5.0"),
                        "decimal_places": 2,
                        "display_order": 5,
                    },
                ],
            },
            "ESR": {
                "category": categories["Hematology"],
                "test_code": "ESR",
                "test_name": "Erythrocyte Sedimentation Rate",
                "loinc_code": "30341-2",
                "sample_type": "EDTA Blood",
                "sample_volume": "2 mL",
                "price": Decimal("300.00"),
                "turnaround_time": 2,
                "parameters": [
                    {
                        "parameter_name": "ESR",
                        "loinc_code": "30341-2",
                        "unit": "mm/hr",
                        "reference_min_male": Decimal("0"),
                        "reference_max_male": Decimal("15"),
                        "reference_min_female": Decimal("0"),
                        "reference_max_female": Decimal("20"),
                        "decimal_places": 0,
                        "display_order": 1,
                    },
                ],
            },
            # Clinical Chemistry
            "GLUCOSE": {
                "category": categories["Clinical Chemistry"],
                "test_code": "GLUCOSE",
                "test_name": "Blood Glucose (Fasting)",
                "loinc_code": "2339-0",
                "sample_type": "Serum",
                "sample_volume": "2 mL",
                "price": Decimal("300.00"),
                "turnaround_time": 2,
                "parameters": [
                    {
                        "parameter_name": "Glucose (Fasting)",
                        "loinc_code": "2339-0",
                        "unit": "mg/dL",
                        "reference_min_male": Decimal("70"),
                        "reference_max_male": Decimal("100"),
                        "reference_min_female": Decimal("70"),
                        "reference_max_female": Decimal("100"),
                        "critical_low": Decimal("40"),
                        "critical_high": Decimal("400"),
                        "decimal_places": 0,
                        "display_order": 1,
                    },
                ],
            },
            "CREATININE": {
                "category": categories["Clinical Chemistry"],
                "test_code": "CREATININE",
                "test_name": "Serum Creatinine",
                "loinc_code": "2160-0",
                "sample_type": "Serum",
                "sample_volume": "2 mL",
                "price": Decimal("400.00"),
                "turnaround_time": 2,
                "parameters": [
                    {
                        "parameter_name": "Creatinine",
                        "loinc_code": "2160-0",
                        "unit": "mg/dL",
                        "reference_min_male": Decimal("0.7"),
                        "reference_max_male": Decimal("1.3"),
                        "reference_min_female": Decimal("0.6"),
                        "reference_max_female": Decimal("1.1"),
                        "critical_high": Decimal("5.0"),
                        "decimal_places": 2,
                        "display_order": 1,
                    },
                ],
            },
            "UREA": {
                "category": categories["Clinical Chemistry"],
                "test_code": "UREA",
                "test_name": "Blood Urea Nitrogen",
                "loinc_code": "3094-0",
                "sample_type": "Serum",
                "sample_volume": "2 mL",
                "price": Decimal("400.00"),
                "turnaround_time": 2,
                "parameters": [
                    {
                        "parameter_name": "Urea",
                        "loinc_code": "3094-0",
                        "unit": "mg/dL",
                        "reference_min_male": Decimal("15"),
                        "reference_max_male": Decimal("45"),
                        "reference_min_female": Decimal("15"),
                        "reference_max_female": Decimal("45"),
                        "critical_high": Decimal("100"),
                        "decimal_places": 1,
                        "display_order": 1,
                    },
                ],
            },
            "ALT": {
                "category": categories["Clinical Chemistry"],
                "test_code": "ALT",
                "test_name": "Alanine Aminotransferase",
                "loinc_code": "1742-6",
                "sample_type": "Serum",
                "sample_volume": "2 mL",
                "price": Decimal("400.00"),
                "turnaround_time": 4,
                "parameters": [
                    {
                        "parameter_name": "ALT",
                        "loinc_code": "1742-6",
                        "unit": "U/L",
                        "reference_min_male": Decimal("10"),
                        "reference_max_male": Decimal("40"),
                        "reference_min_female": Decimal("7"),
                        "reference_max_female": Decimal("35"),
                        "critical_high": Decimal("500"),
                        "decimal_places": 0,
                        "display_order": 1,
                    },
                ],
            },
            "AST": {
                "category": categories["Clinical Chemistry"],
                "test_code": "AST",
                "test_name": "Aspartate Aminotransferase",
                "loinc_code": "1920-8",
                "sample_type": "Serum",
                "sample_volume": "2 mL",
                "price": Decimal("400.00"),
                "turnaround_time": 4,
                "parameters": [
                    {
                        "parameter_name": "AST",
                        "loinc_code": "1920-8",
                        "unit": "U/L",
                        "reference_min_male": Decimal("15"),
                        "reference_max_male": Decimal("40"),
                        "reference_min_female": Decimal("13"),
                        "reference_max_female": Decimal("35"),
                        "critical_high": Decimal("500"),
                        "decimal_places": 0,
                        "display_order": 1,
                    },
                ],
            },
            "ALP": {
                "category": categories["Clinical Chemistry"],
                "test_code": "ALP",
                "test_name": "Alkaline Phosphatase",
                "loinc_code": "6768-6",
                "sample_type": "Serum",
                "sample_volume": "2 mL",
                "price": Decimal("400.00"),
                "turnaround_time": 4,
                "parameters": [
                    {
                        "parameter_name": "ALP",
                        "loinc_code": "6768-6",
                        "unit": "U/L",
                        "reference_min_male": Decimal("40"),
                        "reference_max_male": Decimal("130"),
                        "reference_min_female": Decimal("35"),
                        "reference_max_female": Decimal("105"),
                        "decimal_places": 0,
                        "display_order": 1,
                    },
                ],
            },
            "BILIRUBIN_TOTAL": {
                "category": categories["Clinical Chemistry"],
                "test_code": "BILIRUBIN-T",
                "test_name": "Total Bilirubin",
                "loinc_code": "1975-2",
                "sample_type": "Serum",
                "sample_volume": "2 mL",
                "price": Decimal("400.00"),
                "turnaround_time": 4,
                "parameters": [
                    {
                        "parameter_name": "Total Bilirubin",
                        "loinc_code": "1975-2",
                        "unit": "mg/dL",
                        "reference_min_male": Decimal("0.2"),
                        "reference_max_male": Decimal("1.2"),
                        "reference_min_female": Decimal("0.2"),
                        "reference_max_female": Decimal("1.2"),
                        "critical_high": Decimal("10.0"),
                        "decimal_places": 2,
                        "display_order": 1,
                    },
                ],
            },
            "CHOLESTEROL": {
                "category": categories["Clinical Chemistry"],
                "test_code": "CHOL",
                "test_name": "Total Cholesterol",
                "loinc_code": "2093-3",
                "sample_type": "Serum",
                "sample_volume": "2 mL",
                "price": Decimal("500.00"),
                "turnaround_time": 4,
                "parameters": [
                    {
                        "parameter_name": "Total Cholesterol",
                        "loinc_code": "2093-3",
                        "unit": "mg/dL",
                        "reference_min_male": Decimal("0"),
                        "reference_max_male": Decimal("200"),
                        "reference_min_female": Decimal("0"),
                        "reference_max_female": Decimal("200"),
                        "critical_high": Decimal("300"),
                        "decimal_places": 0,
                        "display_order": 1,
                    },
                ],
            },
            "TRIGLYCERIDES": {
                "category": categories["Clinical Chemistry"],
                "test_code": "TRIG",
                "test_name": "Triglycerides",
                "loinc_code": "2571-8",
                "sample_type": "Serum",
                "sample_volume": "2 mL",
                "price": Decimal("500.00"),
                "turnaround_time": 4,
                "parameters": [
                    {
                        "parameter_name": "Triglycerides",
                        "loinc_code": "2571-8",
                        "unit": "mg/dL",
                        "reference_min_male": Decimal("0"),
                        "reference_max_male": Decimal("150"),
                        "reference_min_female": Decimal("0"),
                        "reference_max_female": Decimal("150"),
                        "critical_high": Decimal("500"),
                        "decimal_places": 0,
                        "display_order": 1,
                    },
                ],
            },
        }

        tests_created = {}
        for test_code, test_data in tests_data.items():
            # Create or get test
            test, created = Test.objects.get_or_create(
                test_code=test_data["test_code"],
                defaults={
                    "category": test_data["category"],
                    "test_name": test_data["test_name"],
                    "loinc_code": test_data.get("loinc_code", ""),
                    "sample_type": test_data["sample_type"],
                    "sample_volume": test_data.get("sample_volume", ""),
                    "price": test_data["price"],
                    "turnaround_time": test_data["turnaround_time"],
                },
            )
            tests_created[test_code] = test
            if created:
                self.stdout.write(f"  Created test: {test.test_code} - {test.test_name}")

            # Create parameters
            for param_data in test_data.get("parameters", []):
                TestParameter.objects.get_or_create(
                    test=test,
                    parameter_name=param_data["parameter_name"],
                    defaults={
                        "loinc_code": param_data.get("loinc_code", ""),
                        "unit": param_data["unit"],
                        "reference_min_male": param_data.get("reference_min_male"),
                        "reference_max_male": param_data.get("reference_max_male"),
                        "reference_min_female": param_data.get("reference_min_female"),
                        "reference_max_female": param_data.get("reference_max_female"),
                        "critical_low": param_data.get("critical_low"),
                        "critical_high": param_data.get("critical_high"),
                        "decimal_places": param_data.get("decimal_places", 2),
                        "display_order": param_data.get("display_order", 0),
                    },
                )

        return tests_created

    def create_panels(self, categories, tests_data):
        """Create test panels."""
        panels_data = [
            {
                "panel_code": "LFT",
                "panel_name": "Liver Function Tests",
                "category": categories["Clinical Chemistry"],
                "sample_type": "Serum",
                "sample_volume": "3 mL",
                "price": Decimal("1500.00"),
                "turnaround_time": 4,
                "test_codes": ["ALT", "AST", "ALP", "BILIRUBIN_TOTAL"],
            },
            {
                "panel_code": "RFT",
                "panel_name": "Renal Function Tests",
                "category": categories["Clinical Chemistry"],
                "sample_type": "Serum",
                "sample_volume": "3 mL",
                "price": Decimal("800.00"),
                "turnaround_time": 2,
                "test_codes": ["UREA", "CREATININE"],
            },
            {
                "panel_code": "LIPID",
                "panel_name": "Lipid Profile",
                "category": categories["Clinical Chemistry"],
                "sample_type": "Serum",
                "sample_volume": "3 mL",
                "price": Decimal("1200.00"),
                "turnaround_time": 4,
                "test_codes": ["CHOLESTEROL", "TRIGLYCERIDES"],
            },
        ]

        for panel_data in panels_data:
            panel, created = TestPanel.objects.get_or_create(
                panel_code=panel_data["panel_code"],
                defaults={
                    "panel_name": panel_data["panel_name"],
                    "category": panel_data["category"],
                    "sample_type": panel_data["sample_type"],
                    "sample_volume": panel_data.get("sample_volume", ""),
                    "price": panel_data["price"],
                    "turnaround_time": panel_data["turnaround_time"],
                },
            )

            # Add tests to panel
            for test_code in panel_data["test_codes"]:
                if test_code in tests_data:
                    panel.tests.add(tests_data[test_code])

            if created:
                self.stdout.write(f"  Created panel: {panel.panel_code} - {panel.panel_name}")

