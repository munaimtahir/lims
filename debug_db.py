
import os
import django
from django.conf import settings
from django.db import connection
import sys

print('Checking DB connection...')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        row = cursor.fetchone()
        print(f'Success: {row}')
except Exception as e:
    print(f'Error: {e}')
    # Print DB settings
    print(f'DB Settings: {settings.DATABASES}')

