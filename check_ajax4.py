import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import User, Account
from financial.models import Sale, Store
for u in User.objects.all():
    print(f'User: {u.username}, Stores: {u.stores.all()}')
