"""Django management command to import LIMS master data from Excel file."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import (
    Parameter,
    ParameterQuickText,
    ReferenceRange,
    Test,
    TestParameter,
)


class Command(BaseCommand):
    """Import LIMS master data from Excel file."""

    help = (
        "Import LIMS master data (Tests, Parameters, Reference Ranges, "
        "etc.) from Excel file"
    )

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--file",
            type=str,
            default="seed_data/AlShifa_LIMS_Master.xlsx",
            help="Path to Excel file (default: seed_data/AlShifa_LIMS_Master.xlsx)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate data without saving to database",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        file_path = options["file"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No data will be saved")
            )

        try:
            # Read Excel file
            self.stdout.write(f"Reading Excel file: {file_path}")
            xls = pd.ExcelFile(file_path)

            # Read all sheets
            df_params = pd.read_excel(xls, "Parameters")
            df_tests = pd.read_excel(xls, "Tests")
            df_tp = pd.read_excel(xls, "Test_Parameters")
            df_rr = pd.read_excel(xls, "Reference_Ranges")
            df_qt = pd.read_excel(xls, "Parameter_Quick_Text")

            self.stdout.write(
                self.style.SUCCESS(
                    f"Loaded sheets: Parameters({len(df_params)}), "
                    f"Tests({len(df_tests)}), "
                    f"Test_Parameters({len(df_tp)}), "
                    f"Reference_Ranges({len(df_rr)}), "
                    f"Parameter_Quick_Text({len(df_qt)})"
                )
            )

            # Replace NaN with None
            df_params = df_params.where(pd.notna(df_params), None)
            df_tests = df_tests.where(pd.notna(df_tests), None)
            df_tp = df_tp.where(pd.notna(df_tp), None)
            df_rr = df_rr.where(pd.notna(df_rr), None)
            df_qt = df_qt.where(pd.notna(df_qt), None)

            # Start transaction
            with transaction.atomic():
                # Import in order: Parameters -> Tests -> Reference Ranges
                # -> Quick Text -> Test Parameters
                params_created, params_updated = self.import_parameters(df_params)
                tests_created, tests_updated = self.import_tests(df_tests)
                rr_created, rr_updated = self.import_reference_ranges(df_rr)
                qt_created, qt_updated = self.import_quick_texts(df_qt)
                tp_created, tp_updated = self.import_test_parameters(df_tp)

                # Print summary
                self.stdout.write(self.style.SUCCESS("\n" + "=" * 80))
                self.stdout.write(self.style.SUCCESS("IMPORT SUMMARY:"))
                self.stdout.write(
                    f"  Parameters:       {params_created} created, "
                    f"{params_updated} updated"
                )
                self.stdout.write(
                    f"  Tests:            {tests_created} created, "
                    f"{tests_updated} updated"
                )
                self.stdout.write(
                    f"  Reference Ranges: {rr_created} created, {rr_updated} updated"
                )
                self.stdout.write(
                    f"  Quick Texts:      {qt_created} created, {qt_updated} updated"
                )
                self.stdout.write(
                    f"  Test Parameters:  {tp_created} created, {tp_updated} updated"
                )
                self.stdout.write(self.style.SUCCESS("=" * 80))

                if dry_run:
                    raise CommandError("Dry-run complete - rolling back transaction")

            self.stdout.write(self.style.SUCCESS("\nImport completed successfully!"))

        except CommandError:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING("\nDry-run completed - no data was saved")
                )
            raise
        except Exception as e:
            raise CommandError(f"Error during import: {str(e)}") from e

    def import_parameters(self, df):
        """Import parameters from DataFrame."""
        self.stdout.write("\nImporting Parameters...")
        created = 0
        updated = 0

        for _, row in df.iterrows():
            code = row.get("Parameter_Code")
            if not code:
                continue

            # Convert boolean fields
            is_calc = self._str_to_bool(row.get("Is_Calculated"))
            has_qt = self._str_to_bool(row.get("Has_Quick_Text"))
            active = self._str_to_bool(row.get("Active"))

            # Parse decimal places
            decimal_places = self._parse_int(row.get("Decimal_Places"))

            obj, is_created = Parameter.objects.update_or_create(
                code=code,
                defaults={
                    "name": row.get("Parameter_Name") or "",
                    "short_name": row.get("Short_Name") or "",
                    "unit": row.get("Default_Unit") or "",
                    "data_type": row.get("Data_Type") or "Numeric",
                    "editor_type": row.get("Editor_Type") or "Plain",
                    "decimal_places": decimal_places,
                    "allowed_values": row.get("Allowed_Values") or "",
                    "is_calculated": is_calc,
                    "calculation_formula": row.get("Calculation_Formula") or "",
                    "flag_direction": row.get("Default_Flagging_Direction") or "Both",
                    "has_quick_text": has_qt,
                    "external_code_type": row.get("External_Code_Type") or "",
                    "external_code_value": row.get("External_Code_Value") or "",
                    "active": active,
                },
            )

            if is_created:
                created += 1
            else:
                updated += 1

        return created, updated

    def import_tests(self, df):
        """Import tests from DataFrame."""
        self.stdout.write("\nImporting Tests...")
        created = 0
        updated = 0

        for _, row in df.iterrows():
            code = row.get("Test_Code")
            if not code:
                continue

            # Convert boolean fields
            active = self._str_to_bool(row.get("Active"))

            # Parse numeric fields
            tat_minutes = self._parse_int(row.get("Default_TAT_Minutes"), default=0)
            charge = self._parse_decimal(row.get("Default_Charge"), default=0)

            obj, is_created = Test.objects.update_or_create(
                code=code,
                defaults={
                    "name": row.get("Test_Name") or "",
                    "short_name": row.get("Short_Name") or "",
                    "test_type": row.get("Test_Type") or "Single",
                    "department": row.get("Department") or "",
                    "specimen_type": row.get("Specimen_Type") or "",
                    "container_type": row.get("Container_Type") or "",
                    "result_scale": row.get("Result_Scale") or "",
                    "default_method": row.get("Default_Method") or "",
                    "default_tat_minutes": tat_minutes,
                    "default_print_group": row.get("Default_Print_Group") or "",
                    "default_report_template": row.get("Default_Report_Template") or "",
                    "default_printer_code": row.get("Default_Printer_Code") or "",
                    "billing_code": row.get("Billing_Code") or "",
                    "default_charge": charge,
                    "external_code_type": row.get("External_Code_Type") or "",
                    "external_code_value": row.get("External_Code_Value") or "",
                    "active": active,
                },
            )

            if is_created:
                created += 1
            else:
                updated += 1

        return created, updated

    def import_reference_ranges(self, df):
        """Import reference ranges from DataFrame."""
        self.stdout.write("\nImporting Reference Ranges...")
        created = 0
        updated = 0
        skipped = 0

        for _, row in df.iterrows():
            param_code = row.get("Parameter_Code")
            if not param_code:
                continue

            # Find parameter
            try:
                parameter = Parameter.objects.get(code=param_code)
            except Parameter.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"  WARNING: Parameter {param_code} not found, "
                        f"skipping reference range"
                    )
                )
                skipped += 1
                continue

            # Parse numeric fields
            age_min = self._parse_int(row.get("Age_Min"), default=0)
            age_max = self._parse_int(row.get("Age_Max"), default=999)
            normal_low = self._parse_decimal(row.get("Normal_Low"))
            normal_high = self._parse_decimal(row.get("Normal_High"))
            critical_low = self._parse_decimal(row.get("Critical_Low"))
            critical_high = self._parse_decimal(row.get("Critical_High"))

            # Parse dates
            effective_from = self._parse_date(row.get("Effective_From"))
            effective_to = self._parse_date(row.get("Effective_To"))

            # Build filter criteria for natural key
            filters = {
                "parameter": parameter,
                "method_code": row.get("Method_Code") or "",
                "sex": row.get("Sex") or "All",
                "age_min": age_min,
                "age_max": age_max,
                "age_unit": row.get("Age_Unit") or "Years",
                "population_group": row.get("Population_Group") or "Adult",
            }

            obj, is_created = ReferenceRange.objects.update_or_create(
                **filters,
                defaults={
                    "unit": row.get("Unit") or "",
                    "normal_low": normal_low,
                    "normal_high": normal_high,
                    "critical_low": critical_low,
                    "critical_high": critical_high,
                    "reference_text": row.get("Reference_Text") or "",
                    "effective_from": effective_from,
                    "effective_to": effective_to,
                },
            )

            if is_created:
                created += 1
            else:
                updated += 1

        if skipped > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"  Skipped {skipped} reference ranges due to missing parameters"
                )
            )

        return created, updated

    def import_quick_texts(self, df):
        """Import parameter quick texts from DataFrame."""
        self.stdout.write("\nImporting Parameter Quick Texts...")
        created = 0
        updated = 0
        skipped = 0

        for _, row in df.iterrows():
            param_code = row.get("Parameter_Code")
            if not param_code:
                continue

            # Find parameter
            try:
                parameter = Parameter.objects.get(code=param_code)
            except Parameter.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"  WARNING: Parameter {param_code} not found, "
                        f"skipping quick text"
                    )
                )
                skipped += 1
                continue

            # Convert boolean fields
            is_default = self._str_to_bool(row.get("Is_Default"))
            active = self._str_to_bool(row.get("Active"))

            title = row.get("Template_Title") or ""
            language = row.get("Language") or "EN"

            obj, is_created = ParameterQuickText.objects.update_or_create(
                parameter=parameter,
                template_title=title,
                language=language,
                defaults={
                    "template_body": row.get("Template_Body") or "",
                    "is_default": is_default,
                    "active": active,
                },
            )

            if is_created:
                created += 1
            else:
                updated += 1

        if skipped > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"  Skipped {skipped} quick texts due to missing parameters"
                )
            )

        return created, updated

    def import_test_parameters(self, df):
        """Import test-parameter relationships from DataFrame."""
        self.stdout.write("\nImporting Test-Parameter Relationships...")
        created = 0
        updated = 0
        skipped = 0

        for _, row in df.iterrows():
            test_code = row.get("Test_Code")
            param_code = row.get("Parameter_Code")

            if not test_code or not param_code:
                continue

            # Find test and parameter
            try:
                test = Test.objects.get(code=test_code)
            except Test.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"  WARNING: Test {test_code} not found, "
                        f"skipping test-parameter mapping"
                    )
                )
                skipped += 1
                continue

            try:
                parameter = Parameter.objects.get(code=param_code)
            except Parameter.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"  WARNING: Parameter {param_code} not found, "
                        f"skipping test-parameter mapping"
                    )
                )
                skipped += 1
                continue

            # Convert boolean fields
            is_mandatory = self._str_to_bool(row.get("Is_Mandatory"), default=True)
            show_on_report = self._str_to_bool(row.get("Show_On_Report"), default=True)
            delta_check = self._str_to_bool(row.get("Delta_Check_Enabled"))

            # Parse numeric fields
            display_order = self._parse_int(row.get("Display_Order"), default=0)
            panic_low = self._parse_decimal(row.get("Panic_Low_Override"))
            panic_high = self._parse_decimal(row.get("Panic_High_Override"))

            obj, is_created = TestParameter.objects.update_or_create(
                test=test,
                parameter=parameter,
                defaults={
                    "display_order": display_order,
                    "section_header": row.get("Section_Header") or "",
                    "is_mandatory": is_mandatory,
                    "show_on_report": show_on_report,
                    "default_reference_profile_id": row.get(
                        "Default_Reference_Profile_ID"
                    )
                    or "",
                    "delta_check_enabled": delta_check,
                    "panic_low_override": panic_low,
                    "panic_high_override": panic_high,
                    "comment_template_id": row.get("Comment_Template_ID") or "",
                },
            )

            if is_created:
                created += 1
            else:
                updated += 1

        if skipped > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"  Skipped {skipped} test-parameter mappings due to "
                    f"missing tests or parameters"
                )
            )

        return created, updated

    # Helper methods

    def _str_to_bool(self, value, default=False):
        """Convert string value to boolean."""
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ["yes", "true", "1", "y"]
        return default

    def _parse_int(self, value, default=None):
        """Parse integer value safely."""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _parse_decimal(self, value, default=None):
        """Parse decimal value safely."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default
        try:
            return Decimal(str(value))
        except (ValueError, TypeError, InvalidOperation):
            return default

    def _parse_date(self, value):
        """Parse date value safely."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value).date()
            except (ValueError, TypeError):
                pass
        return None
