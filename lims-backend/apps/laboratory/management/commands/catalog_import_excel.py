from django.core.management.base import BaseCommand
from apps.laboratory.utils import import_tests_from_excel
import json

class Command(BaseCommand):
    help = "Import catalog from Excel using standard contract"

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, required=True, help='Path to Excel file')
        parser.add_argument('--dry-run', action='store_true', help='Perform a dry run verification')

    def handle(self, *args, **options):
        path = options['path']
        dry_run = options['dry_run']
        
        self.stdout.write(f"Importing from {path} (Dry Run: {dry_run})...")
        
        try:
            summary = import_tests_from_excel(path, dry_run=dry_run)
            
            # Print summary clearly
            self.stdout.write("--- Import Summary ---")
            self.stdout.write(f"Tests Created: {summary.get('tests_created', 0)}")
            self.stdout.write(f"Tests Updated: {summary.get('tests_updated', 0)}")
            self.stdout.write(f"Parameters Created: {summary.get('parameters_created', 0)}")
            self.stdout.write(f"Mappings Created: {summary.get('mappings_created', 0)}")
            self.stdout.write(f"Reference Ranges: {summary.get('ranges_created', 0)}")
            
            if summary.get('errors'):
                self.stdout.write(self.style.ERROR(f"Errors Found: {len(summary['errors'])}"))
                for err in summary['errors'][:10]:
                    self.stdout.write(f"  {err}")
                if len(summary['errors']) > 10:
                    self.stdout.write("  ... and more check logs.")
            
            if summary.get("validation_passed", True):
                self.stdout.write(self.style.SUCCESS("IMPORT SUCCESS"))
            else:
                self.stdout.write(self.style.ERROR("IMPORT COMPLETED WITH ERRORS"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"CRITICAL FAILURE: {e}"))
            import traceback
            traceback.print_exc()
