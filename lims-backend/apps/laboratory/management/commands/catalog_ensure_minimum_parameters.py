"""
Management command to ensure all active tests have at least one parameter mapping.

This command:
1. Finds tests with no parameter mappings
2. Creates a default parameter mapping for each (using p998 or p999)
3. Uses p999 for qualitative tests (ELISA, Rapid, Screen, etc.)
4. Uses p998 for all other tests

Usage:
    python manage.py catalog_ensure_minimum_parameters [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.laboratory.models import Parameter, Test, TestParameter


class Command(BaseCommand):
    help = "Ensure all active tests have at least one parameter mapping"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry run without making changes",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        dry_run = options["dry_run"]

        self.stdout.write(self.style.WARNING(f"\n{'='*60}"))
        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )
        else:
            self.stdout.write(
                self.style.WARNING("EXECUTION MODE - Changes will be committed")
            )
        self.stdout.write(self.style.WARNING(f"{'='*60}\n"))

        # Get all active tests
        active_tests = Test.objects.filter(is_active=True)
        total_tests = active_tests.count()

        self.stdout.write(f"Total active tests: {total_tests}\n")

        # Find tests without mappings
        tests_without_mappings = []
        for test in active_tests:
            if not TestParameter.objects.filter(test=test).exists():
                tests_without_mappings.append(test)

        if not tests_without_mappings:
            self.stdout.write(
                self.style.SUCCESS(
                    "✓ All active tests already have parameter mappings\n"
                )
            )
            return 0

        self.stdout.write(f"Tests without mappings: {len(tests_without_mappings)}\n")

        # Determine which parameter to use for each test
        qualitative_keywords = [
            "elisa",
            "rapid",
            "screen",
            "vdrl",
            "hbsag",
            "hiv",
            "hcv",
            "dengue",
            "typhidot",
            "malaria",
            "pregnancy",
            "covid",
            "h.pylori",
            "qualitative",
            "serology",
            "antibody",
            "antigen",
        ]

        tests_for_p_qual = []
        tests_for_p_result = []

        for test in tests_without_mappings:
            test_name_lower = test.test_name.lower()
            is_qualitative = any(
                keyword in test_name_lower for keyword in qualitative_keywords
            )

            if is_qualitative:
                tests_for_p_qual.append(test)
            else:
                tests_for_p_result.append(test)

        self.stdout.write(
            f"  Qualitative tests (will use p999): {len(tests_for_p_qual)}"
        )
        self.stdout.write(f"  Other tests (will use p998): {len(tests_for_p_result)}\n")

        # Create or get default parameters
        # Use p999 for qualitative and p998 for general result
        # These are high numbers to avoid conflicts with real parameters
        if not dry_run:
            with transaction.atomic():
                # Check if p998 or p999 already exist with different meanings
                existing_p998 = Parameter.objects.filter(parameter_id="p998").first()
                existing_p999 = Parameter.objects.filter(parameter_id="p999").first()

                if existing_p998 and existing_p998.parameter_name != "Result":
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ WARNING: p998 already exists with name '{existing_p998.parameter_name}'"
                        )
                    )

                if existing_p999 and existing_p999.parameter_name != "Result":
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ WARNING: p999 already exists with name '{existing_p999.parameter_name}'"
                        )
                    )

                # Create p999 parameter for qualitative tests if needed
                if tests_for_p_qual:
                    p_qual, created = Parameter.objects.get_or_create(
                        parameter_id="p999",
                        defaults={
                            "parameter_name": "Result",
                            "unit": "",
                            "data_type": "Text",
                            "active": True,
                        },
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                "  ✓ Created parameter: p999 (qualitative)"
                            )
                        )
                    else:
                        self.stdout.write("  → Using existing parameter: p999")

                # Create p998 parameter for general result if needed
                if tests_for_p_result:
                    p_result, created = Parameter.objects.get_or_create(
                        parameter_id="p998",
                        defaults={
                            "parameter_name": "Result",
                            "unit": "",
                            "data_type": "Text",
                            "active": True,
                        },
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                "  ✓ Created parameter: p998 (general result)"
                            )
                        )
                    else:
                        self.stdout.write("  → Using existing parameter: p998")

                # Create mappings for qualitative tests
                mappings_created = 0
                for test in tests_for_p_qual:
                    TestParameter.objects.get_or_create(
                        test=test,
                        parameter=p_qual,
                        defaults={"display_order": 1, "reportable": True},
                    )
                    mappings_created += 1

                # Create mappings for other tests
                for test in tests_for_p_result:
                    TestParameter.objects.get_or_create(
                        test=test,
                        parameter=p_result,
                        defaults={"display_order": 1, "reportable": True},
                    )
                    mappings_created += 1

                self.stdout.write(f"\n✓ Created {mappings_created} parameter mappings")
        else:
            self.stdout.write("\n[DRY RUN] Would create:")
            if tests_for_p_qual:
                self.stdout.write(f"  - Parameter: p999 (if not exists)")
                self.stdout.write(f"  - {len(tests_for_p_qual)} mappings to p999")
            if tests_for_p_result:
                self.stdout.write(f"  - Parameter: p998 (if not exists)")
                self.stdout.write(f"  - {len(tests_for_p_result)} mappings to p998")

        # Final verification
        self.stdout.write("\n" + "=" * 60)
        remaining_without = (
            Test.objects.filter(is_active=True)
            .exclude(test_parameters__isnull=False)
            .count()
        )

        if remaining_without == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "✓ All active tests now have at least one parameter mapping"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠ {remaining_without} tests still without mappings (may be inactive)"
                )
            )

        self.stdout.write("=" * 60 + "\n")

        return 0
