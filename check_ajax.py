import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.test import RequestFactory
from core.models import User
from financial.views import get_customer_sales
import json

user = User.objects.first()
factory = RequestFactory()
request = factory.get('/financial/ajax/get-customer-sales/0/')
request.user = user
response = get_customer_sales(request, 0)
print('Customer 0:', response.content.decode())

request = factory.get('/financial/ajax/get-customer-sales/1/')
request.user = user
response = get_customer_sales(request, 1)
print('Customer 1:', response.content.decode())

request = factory.get('/financial/ajax/get-customer-sales/2/')
request.user = user
response = get_customer_sales(request, 2)
print('Customer 2:', response.content.decode())
