"""Tests for import_lims_master management command."""

import os
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from catalog.models import Parameter, ReferenceRange, Test, TestParameter


class ImportLIMSMasterCommandTest(TestCase):
    """Test cases for import_lims_master command."""

    def test_command_exists(self):
        """Test that the command can be imported."""
        from catalog.management.commands.import_lims_master import Command

        self.assertIsNotNone(Command)

    def test_command_help(self):
        """Test that the command help works."""
        # --help causes SystemExit, so we need to catch it
        out = StringIO()
        with self.assertRaises(SystemExit) as context:
            call_command("import_lims_master", "--help", stdout=out)
        # Exit code 0 means success
        self.assertEqual(context.exception.code, 0)

    def test_command_with_missing_file(self):
        """Test that command fails gracefully with missing file."""
        with self.assertRaises(CommandError):
            call_command(
                "import_lims_master",
                "--file",
                "/nonexistent/file.xlsx",
                stdout=StringIO(),
                stderr=StringIO(),
            )

    def test_dry_run_with_real_file(self):
        """Test dry-run mode with the actual Excel file."""
        excel_file = "seed_data/AlShifa_LIMS_Master.xlsx"

        # Skip test if file doesn't exist (e.g., in CI environment)
        if not os.path.exists(excel_file):
            self.skipTest("Excel file not found")

        out = StringIO()
        # Dry run should fail with CommandError but not crash
        with self.assertRaises(CommandError) as context:
            call_command(
                "import_lims_master", "--dry-run", "--file", excel_file, stdout=out
            )

        # Check that it's the expected "Dry-run complete" error
        self.assertIn("Dry-run complete", str(context.exception))

        # Verify no data was actually saved
        self.assertEqual(Parameter.objects.count(), 0)
        self.assertEqual(Test.objects.count(), 0)
        self.assertEqual(TestParameter.objects.count(), 0)
        self.assertEqual(ReferenceRange.objects.count(), 0)
