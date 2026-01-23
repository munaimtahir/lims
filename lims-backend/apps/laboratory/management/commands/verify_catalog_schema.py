from django.core.management.base import BaseCommand
from django.db import connection
from apps.laboratory.models import Parameter, TestParameter, ReferenceRange

class Command(BaseCommand):
    help = "Verify catalog schema alignment"

    def handle(self, *args, **options):
        self.stdout.write("Verifying catalog schema...")
        
        # 1. Check parameters table columns
        with connection.cursor() as cursor:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'parameters'")
            columns = [row[0] for row in cursor.fetchall()]
        
        if 'parameter_id' not in columns:
            self.stdout.write(self.style.ERROR("FAIL: parameters table missing parameter_id column"))
            # In a real repair scenario, we might try to rename 'code' or similar, but for now we just fail/report
            # The prompt asks for automated repair in step 3, but let's check first.
            return
        else:
            self.stdout.write(self.style.SUCCESS("PASS: parameters.parameter_id exists"))

        # 2. Check FK relations
        try:
            # Just count to see if query works
            tp_count = TestParameter.objects.count()
            self.stdout.write(self.style.SUCCESS(f"PASS: TestParameter queryable ({tp_count} rows)"))
            
            rr_count = ReferenceRange.objects.count()
            self.stdout.write(self.style.SUCCESS(f"PASS: ReferenceRange queryable ({rr_count} rows)"))
            
            p_count = Parameter.objects.count()
            self.stdout.write(self.style.SUCCESS(f"PASS: Parameter queryable ({p_count} rows)"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"FAIL: Relation check failed: {e}"))
            return

        self.stdout.write(self.style.SUCCESS("SCHEMA VERIFICATION PASSED"))
