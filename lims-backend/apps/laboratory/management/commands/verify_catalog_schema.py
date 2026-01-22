"""
Management command to verify catalog schema and parameter_id integrity.

Usage:
    python manage.py verify_catalog_schema
"""

from django.core.management.base import BaseCommand
from django.db import connection
from apps.laboratory.models import Parameter, Test, TestParameter
import re


class Command(BaseCommand):
    help = "Verify catalog schema and parameter_id integrity"

    def handle(self, *args, **options):
        """Execute the verification checks."""
        self.stdout.write(self.style.WARNING("\n=== Catalog Schema Verification ===\n"))
        
        all_checks_passed = True
        
        # Check 1: Verify parameter_id field exists
        all_checks_passed &= self._check_parameter_id_field_exists()
        
        # Check 2: Verify uniqueness constraint
        all_checks_passed &= self._check_uniqueness_constraint()
        
        # Check 3: Check for missing parameter_ids
        all_checks_passed &= self._check_missing_parameter_ids()
        
        # Check 4: Validate parameter_id format
        all_checks_passed &= self._check_parameter_id_format()
        
        # Check 5: Sample parameter_ids
        self._show_sample_parameter_ids()
        
        # Check 6: Statistics
        self._show_statistics()
        
        # Final result
        self.stdout.write("\n" + "=" * 50)
        if all_checks_passed:
            self.stdout.write(self.style.SUCCESS("\n✓ All verification checks PASSED\n"))
        else:
            self.stdout.write(self.style.ERROR("\n✗ Some verification checks FAILED\n"))
        
        return 0 if all_checks_passed else 1
    
    def _check_parameter_id_field_exists(self):
        """Check if parameter_id field exists in the database."""
        self.stdout.write("\n1. Checking parameter_id field existence...")
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'parameters' AND column_name = 'parameter_id'
            """)
            result = cursor.fetchone()
        
        if result:
            self.stdout.write(self.style.SUCCESS(
                f"   ✓ parameter_id field exists (type: {result[1]})"
            ))
            return True
        else:
            self.stdout.write(self.style.ERROR(
                "   ✗ parameter_id field NOT FOUND in parameters table"
            ))
            return False
    
    def _check_uniqueness_constraint(self):
        """Check if uniqueness constraint exists for parameter_id."""
        self.stdout.write("\n2. Checking uniqueness constraint...")
        
        # Since parameter_id is a primary key, it's automatically unique
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT constraint_name, constraint_type 
                FROM information_schema.table_constraints 
                WHERE table_name = 'parameters' 
                AND constraint_type IN ('PRIMARY KEY', 'UNIQUE')
                AND constraint_name LIKE '%parameter_id%'
            """)
            result = cursor.fetchone()
        
        if result:
            self.stdout.write(self.style.SUCCESS(
                f"   ✓ Uniqueness constraint exists: {result[0]} ({result[1]})"
            ))
            return True
        else:
            # Check if it's the primary key
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT constraint_name
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'parameters' 
                    AND constraint_type = 'PRIMARY KEY'
                """)
                result = cursor.fetchone()
            
            if result:
                self.stdout.write(self.style.SUCCESS(
                    f"   ✓ parameter_id is PRIMARY KEY (automatically unique)"
                ))
                return True
            else:
                self.stdout.write(self.style.WARNING(
                    "   ⚠ Could not verify uniqueness constraint"
                ))
                return False
    
    def _check_missing_parameter_ids(self):
        """Check for parameters with missing parameter_ids."""
        self.stdout.write("\n3. Checking for missing parameter_ids...")
        
        # Count parameters with empty or null parameter_id
        empty_count = Parameter.objects.filter(parameter_id="").count()
        
        if empty_count == 0:
            total_count = Parameter.objects.count()
            self.stdout.write(self.style.SUCCESS(
                f"   ✓ No missing parameter_ids (all {total_count} parameters have IDs)"
            ))
            return True
        else:
            self.stdout.write(self.style.ERROR(
                f"   ✗ Found {empty_count} parameters with missing parameter_id"
            ))
            return False
    
    def _check_parameter_id_format(self):
        """Validate that all parameter_ids match the expected format."""
        self.stdout.write("\n4. Validating parameter_id format (must match p<number>)...")
        
        parameters = Parameter.objects.all()
        invalid_params = []
        pattern = re.compile(r'^p[0-9]+$')
        
        for param in parameters:
            if not pattern.match(param.parameter_id):
                invalid_params.append(param.parameter_id)
        
        if not invalid_params:
            self.stdout.write(self.style.SUCCESS(
                f"   ✓ All {parameters.count()} parameter_ids have valid format"
            ))
            return True
        else:
            self.stdout.write(self.style.ERROR(
                f"   ✗ Found {len(invalid_params)} parameters with invalid format:"
            ))
            for param_id in invalid_params[:10]:  # Show first 10
                self.stdout.write(f"      - {param_id}")
            if len(invalid_params) > 10:
                self.stdout.write(f"      ... and {len(invalid_params) - 10} more")
            return False
    
    def _show_sample_parameter_ids(self):
        """Show sample parameter_ids."""
        self.stdout.write("\n5. Sample parameter_ids:")
        
        parameters = Parameter.objects.order_by("parameter_id")[:10]
        
        if parameters:
            for param in parameters:
                self.stdout.write(
                    f"   - {param.parameter_id}: {param.parameter_name} ({param.unit or 'no unit'})"
                )
        else:
            self.stdout.write(self.style.WARNING("   ⚠ No parameters found in database"))
    
    def _show_statistics(self):
        """Show statistics about the catalog."""
        self.stdout.write("\n6. Catalog Statistics:")
        
        param_count = Parameter.objects.count()
        test_count = Test.objects.count()
        mapping_count = TestParameter.objects.count()
        
        self.stdout.write(f"   - Total Parameters: {param_count}")
        self.stdout.write(f"   - Total Tests: {test_count}")
        self.stdout.write(f"   - Total Test-Parameter Mappings: {mapping_count}")
        
        if param_count > 0:
            active_params = Parameter.objects.filter(active=True).count()
            self.stdout.write(f"   - Active Parameters: {active_params} ({active_params/param_count*100:.1f}%)")
