
import os
import django
import sys

# Setup Django
sys.path.append('/home/munaim/srv/apps/lims/lims-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.laboratory.models import (
    TestCategory, Test, TestParameter, ReferenceRange, 
    TestPanel, Parameter, ParameterReferenceRange, 
    ParameterQuickText, CatalogImportJob
)
from apps.orders.models import Order, OrderItem
from apps.results.models import TestResult

models = [
    ('TestCategory', TestCategory),
    ('Test', Test),
    ('TestParameter', TestParameter),
    ('ReferenceRange', ReferenceRange),
    ('TestPanel', TestPanel),
    ('Parameter', Parameter),
    ('ParameterReferenceRange', ParameterReferenceRange),
    ('ParameterQuickText', ParameterQuickText),
    ('CatalogImportJob', CatalogImportJob),
    ('Order', Order),
    ('OrderItem', OrderItem),
    ('TestResult', TestResult)
]

print("Database Counts:")
for name, model in models:
    try:
        count = model.objects.count()
        print(f"{name}: {count}")
    except Exception as e:
        print(f"{name}: Error - {str(e)}")
