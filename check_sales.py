import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from financial.models import Sale, Customer
c=Customer.objects.filter(name__icontains='Glam').first()
print(f'Cliente: {c}')
if c:
    for s in c.sales.all():
        print(f'Venda: {s.id}, Total: {s.total_amount}, Remaining: {s.remaining_amount}, Status: {s.status}')
