"""
Django management command to seed the test catalog with initial data.

This command creates test categories, tests, parameters, and mappings.
It is idempotent - safe to run multiple times.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.laboratory.models import (
    Parameter,
    ReferenceRange,
    Test,
    TestCategory,
    TestPanel,
    TestParameter,
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
            self.stdout.write(
                self.style.WARNING("Clearing existing test catalog data...")
            )
            ReferenceRange.objects.all().delete()
            TestParameter.objects.all().delete()
            # Clear many-to-many relationships before deleting panels
            for panel in TestPanel.objects.all():
                panel.tests.clear()
            TestPanel.objects.all().delete()
            Test.objects.all().delete()
            Parameter.objects.all().delete()
            TestCategory.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Seeding test catalog..."))

        # Create categories
        categories = self.create_categories()

        # Create global parameters
        parameters = self.create_global_parameters()

        # Create tests and map them
        tests_data = self.create_tests_and_mappings(categories, parameters)

        # Create panels
        self.create_panels(categories, tests_data)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded test catalog: "
                f"{TestCategory.objects.count()} categories, "
                f"{Test.objects.count()} tests, "
                f"{Parameter.objects.count()} global parameters, "
                f"{TestParameter.objects.count()} mappings"
            )
        )

    def create_categories(self):
        """Create test categories."""
        categories_data = [
            {
                "name": "Hematology",
                "description": "Blood cell analysis and related tests",
            },
            {
                "name": "Clinical Chemistry",
                "description": "Biochemistry and metabolic tests",
            },
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

    def create_global_parameters(self):
        """Create global parameters."""
        parameters_data = [
            {"id": "p1", "name": "Hemoglobin", "unit": "g/dL"},
            {"id": "p2", "name": "Hematocrit", "unit": "%"},
            {"id": "p3", "name": "White Blood Cell Count", "unit": "×10³/μL"},
            {"id": "p4", "name": "Platelet Count", "unit": "×10³/μL"},
            {"id": "p5", "name": "Glucose (Fasting)", "unit": "mg/dL"},
            {"id": "p6", "name": "Creatinine", "unit": "mg/dL"},
            {"id": "p7", "name": "Urea", "unit": "mg/dL"},
            {"id": "p8", "name": "ALT", "unit": "U/L"},
            {"id": "p9", "name": "AST", "unit": "U/L"},
            {"id": "p10", "name": "ALP", "unit": "U/L"},
            {"id": "p11", "name": "Total Bilirubin", "unit": "mg/dL"},
        ]

        parameters = {}
        for p_data in parameters_data:
            param, created = Parameter.objects.get_or_create(
                parameter_id=p_data["id"],
                defaults={"parameter_name": p_data["name"], "unit": p_data["unit"]},
            )
            parameters[p_data["id"]] = param
        return parameters

    def create_tests_and_mappings(self, categories, parameters):
        """Create tests and their parameter mappings."""
        tests_data = {
            1: {
                "test_code": "CBC",
                "test_name": "Complete Blood Count",
                "category": categories["Hematology"],
                "price": Decimal("800.00"),
                "tat": 4,
                "mappings": [
                    {"p_id": "p1", "order": 1},
                    {"p_id": "p2", "order": 2},
                    {"p_id": "p3", "order": 3},
                    {"p_id": "p4", "order": 4},
                ],
            },
            2: {
                "test_code": "GLUCOSE",
                "test_name": "Blood Glucose (Fasting)",
                "category": categories["Clinical Chemistry"],
                "price": Decimal("300.00"),
                "tat": 2,
                "mappings": [
                    {"p_id": "p5", "order": 1},
                ],
            },
            3: {
                "test_code": "LFT",
                "test_name": "Liver Function Tests",
                "category": categories["Clinical Chemistry"],
                "price": Decimal("1500.00"),
                "tat": 4,
                "mappings": [
                    {"p_id": "p8", "order": 1},
                    {"p_id": "p9", "order": 2},
                    {"p_id": "p10", "order": 3},
                    {"p_id": "p11", "order": 4},
                ],
            },
        }

        created_tests = {}
        for t_id, t_data in tests_data.items():
            test, created = Test.objects.get_or_create(
                test_id=t_id,
                defaults={
                    "test_code": t_data["test_code"],
                    "test_name": t_data["test_name"],
                    "category": t_data["category"],
                    "price": t_data["price"],
                    "turnaround_time": t_data["tat"],
                    "sample_type": "Serum",
                },
            )
            created_tests[t_data["test_code"]] = test

            for m_data in t_data["mappings"]:
                TestParameter.objects.get_or_create(
                    test=test,
                    parameter=parameters[m_data["p_id"]],
                    defaults={"display_order": m_data["order"]},
                )

        return created_tests

    def create_panels(self, categories, tests_data):
        """Create test panels."""
        panels_data = [
            {
                "panel_code": "P-LFT",
                "panel_name": "Liver Panel",
                "category": categories["Clinical Chemistry"],
                "sample_type": "Serum",
                "price": Decimal("1500.00"),
                "turnaround_time": 4,
                "test_codes": ["LFT"],
            },
        ]

        for panel_data in panels_data:
            panel, created = TestPanel.objects.get_or_create(
                panel_code=panel_data["panel_code"],
                defaults={
                    "panel_name": panel_data["panel_name"],
                    "category": panel_data["category"],
                    "sample_type": panel_data["sample_type"],
                    "price": panel_data["price"],
                    "turnaround_time": panel_data["turnaround_time"],
                },
            )

            for test_code in panel_data["test_codes"]:
                if test_code in tests_data:
                    panel.tests.add(tests_data[test_code])
