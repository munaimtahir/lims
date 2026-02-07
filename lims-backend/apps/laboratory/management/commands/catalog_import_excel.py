"""
Management command to import test catalog from Excel file.

Usage:
    python manage.py catalog_import_excel --path <file.xlsx> [--dry-run]
"""

import os

from django.core.management.base import BaseCommand, CommandError

from apps.laboratory.catalog_io import import_catalog_from_excel


class Command(BaseCommand):
    help = "Import test catalog from Excel file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path", type=str, required=True, help="Path to Excel file to import"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry run without making changes",
        )

    def handle(self, *args, **options):
        """Execute the import."""
        file_path = options["path"]
        dry_run = options["dry_run"]

        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")

        if not file_path.endswith((".xlsx", ".xls")):
            raise CommandError(
                f"File must be an Excel file (.xlsx or .xls): {file_path}"
            )

        self.stdout.write(self.style.WARNING(f"\n{'='*60}"))
        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )
        else:
            self.stdout.write(
                self.style.WARNING("IMPORT MODE - Changes will be committed")
            )
        self.stdout.write(self.style.WARNING(f"{'='*60}\n"))

        self.stdout.write(f"Importing from: {file_path}\n")

        try:
            summary = import_catalog_from_excel(
                file_path,
                strict=True,
                allow_defaults=False,
                mode="upsert",
                dry_run=dry_run,
            )

            # Display summary
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("IMPORT SUMMARY")
            self.stdout.write("=" * 60)

            counts = summary["counts"]
            self.stdout.write(f"\nTests:")
            self.stdout.write(f"  Created: {counts['tests']['created']}")
            self.stdout.write(f"  Updated: {counts['tests']['updated']}")
            self.stdout.write(f"  Unchanged: {counts['tests']['unchanged']}")

            self.stdout.write(f"\nParameters:")
            self.stdout.write(f"  Created: {counts['parameters']['created']}")
            self.stdout.write(f"  Updated: {counts['parameters']['updated']}")
            self.stdout.write(f"  Unchanged: {counts['parameters']['unchanged']}")

            self.stdout.write(f"\nMappings:")
            self.stdout.write(f"  Created: {counts['mappings']['created']}")
            self.stdout.write(f"  Updated: {counts['mappings']['updated']}")
            self.stdout.write(f"  Unchanged: {counts['mappings']['unchanged']}")

            self.stdout.write(f"\nReference Ranges:")
            self.stdout.write(f"  Created: {counts['reference_ranges']['created']}")
            self.stdout.write(f"  Updated: {counts['reference_ranges']['updated']}")
            self.stdout.write(f"  Unchanged: {counts['reference_ranges']['unchanged']}")

            # Display errors if any
            if summary["errors"]:
                self.stdout.write(
                    self.style.ERROR(f"\n\nERRORS ({len(summary['errors'])}):")
                )
                for error in summary["errors"][:20]:  # Show first 20
                    self.stdout.write(
                        self.style.ERROR(
                            f"  [{error['sheet']}] Row {error['row']}: {error['message']}"
                        )
                    )
                if len(summary["errors"]) > 20:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ... and {len(summary['errors']) - 20} more errors"
                        )
                    )

            # Final status
            self.stdout.write("\n" + "=" * 60)
            if not summary["errors"]:
                self.stdout.write(self.style.SUCCESS("✓ Import completed successfully"))
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING("  (Dry run - no changes were made)")
                    )
            else:
                self.stdout.write(self.style.ERROR("✗ Import completed with errors"))
                self.stdout.write(
                    self.style.WARNING("  Review errors above before importing")
                )

            self.stdout.write("=" * 60 + "\n")

            return 0 if not summary["errors"] else 1

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\n✗ Import failed with error: {str(e)}")
            )
            import traceback

            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise CommandError(f"Import failed: {str(e)}")
