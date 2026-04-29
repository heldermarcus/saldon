import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from financial.models import Sale, Store
store = Store.objects.first()
print('Store:', store)
sales = Sale.objects.exclude(status='paid')
print('All pending sales:', sales)
for s in sales:
    print('Sale:', s.id, 'Store:', s.store, 'Customer:', s.customer)
