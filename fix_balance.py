import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import Account
from financial.models import Transaction
from django.db.models import Sum

for account in Account.objects.all():
    incomes = Transaction.objects.filter(account=account, type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = Transaction.objects.filter(account=account, type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    account.balance = incomes - expenses
    account.save()
    print(f"Conta {account.name} corrigida. Novo saldo: {account.balance}")
