import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from financial.models import Sale, Store
store = Store.objects.first()
print('Store:', store)
sales = Sale.objects.filter(store=store).exclude(status='paid')
print('Sales:', sales)
