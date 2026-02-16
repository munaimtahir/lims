
import os
import django
import sys

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.laboratory.models import (
    TestCategory, Test, TestParameter, ReferenceRange, 
    TestPanel, Parameter, ParameterReferenceRange, 
    ParameterQuickText, CatalogImportJob
)
from apps.orders.models import Order, OrderItem
from apps.results.models import TestResult
from apps.samples.models import Sample, SampleCollection
from apps.billing.models import Payment

def clear_data():
    print("Starting data clearance...")
    
    # 1. Clear Results and Orders first due to PROTECT constraints
    print("Clearing TestResult...")
    TestResult.objects.all().delete()
    
    print("Clearing Sample...")
    Sample.objects.all().delete()
    
    print("Clearing SampleCollection...")
    SampleCollection.objects.all().delete()
    
    print("Clearing OrderItem...")
    OrderItem.objects.all().delete()
    
    print("Clearing Payment...")
    Payment.objects.all().delete()
    
    print("Clearing Order...")
    Order.objects.all().delete()
    
    # 2. Clear Catalog Data
    print("Clearing CatalogImportJob...")
    CatalogImportJob.objects.all().delete()
    
    print("Clearing TestParameter...")
    TestParameter.objects.all().delete()
    
    print("Clearing ReferenceRange...")
    ReferenceRange.objects.all().delete()
    
    print("Clearing ParameterReferenceRange...")
    ParameterReferenceRange.objects.all().delete()
    
    print("Clearing ParameterQuickText...")
    ParameterQuickText.objects.all().delete()
    
    print("Clearing TestPanel...")
    TestPanel.objects.all().delete()
    
    print("Clearing Test...")
    Test.objects.all().delete()
    
    print("Clearing Parameter...")
    Parameter.objects.all().delete()
    
    print("Clearing TestCategory...")
    TestCategory.objects.all().delete()
    
    print("Data clearance complete.")

if __name__ == "__main__":
    clear_data()

