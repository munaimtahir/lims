from django.core.management.base import BaseCommand
from apps.laboratory.models import Test, Parameter, TestParameter
from django.db.models import Count

class Command(BaseCommand):
    help = "Ensure every test has at least one parameter mapping"

    def handle(self, *args, **options):
        self.stdout.write("Ensuring minimum parameters for all tests...")

        # 1. Setup default parameters
        p_result, _ = Parameter.objects.get_or_create(
            parameter_id="p_result",
            defaults={
                "parameter_name": "Result",
                "unit": "",
                "data_type": "Numeric",
                "active": True
            }
        )
        
        p_qual, _ = Parameter.objects.get_or_create(
            parameter_id="p_qual",
            defaults={
                "parameter_name": "Result",
                "unit": "",
                "data_type": "Text",
                "active": True
            }
        )
        
        qual_keywords = [
            "ELISA", "RAPID", "SCREEN", "VDRL", "HBSAG", "HIV", "HCV", 
            "DENGUE", "TYPHIDOT", "MALARIA", "PREGNANCY", "COVID", "H.PYLORI"
        ]

        # 2. Iterate tests
        # Optimize: get tests with 0 parameters
        tests_without_params = Test.objects.annotate(pc=Count('test_parameters')).filter(pc=0)
        
        count = 0
        fixed_qual = 0
        
        for test in tests_without_params:
            t_name_upper = test.test_name.upper()
            is_qual = any(k in t_name_upper for k in qual_keywords)
            
            target_param = p_qual if is_qual else p_result
            
            TestParameter.objects.create(
                test=test,
                parameter=target_param,
                display_order=1,
                reportable=True
            )
            
            if is_qual: fixed_qual += 1
            count += 1
            
            if count % 50 == 0:
                self.stdout.write(f"Processed {count} tests...")

        self.stdout.write(self.style.SUCCESS(f"Done. Fixed {count} tests ({fixed_qual} qualitative, {count - fixed_qual} numeric/default)."))
