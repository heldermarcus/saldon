from django.db import models
from django.conf import settings
from core.models import User, Store, Account

class Category(models.Model):
    TYPE_CHOICES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )
    ACCOUNT_TYPE_CHOICES = (
        ('PF', 'PF'),
        ('PJ', 'PJ'),
        ('both', 'Both'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    account_type = models.CharField(max_length=4, choices=ACCOUNT_TYPE_CHOICES)
    is_fixed_cost = models.BooleanField(default=False)
    icon = models.CharField(max_length=50, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Customer(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    total_debt = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_blocked = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TYPE_CHOICES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('pix', 'PIX'),
        ('card', 'Card'),
        ('check', 'Check'),
        ('promissory', 'Promissory'),
        ('installment', 'Installment'),
    )
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=500, blank=True)
    date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.type} - {self.amount} - {self.date}"

class Sale(models.Model):
    PAYMENT_TYPE_CHOICES = (
        ('check', 'Check'),
        ('promissory', 'Promissory'),
        ('installment', 'Installment'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    )
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='sales')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sales')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2)
    installments_count = models.IntegerField(default=1)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sale_date = models.DateField()
    first_due_date = models.DateField()
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.remaining_amount = self.total_amount - self.paid_amount
        if self.remaining_amount <= 0:
            self.status = 'paid'
        super().save(*args, **kwargs)

class SaleInstallment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    )
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='installments')
    installment_number = models.IntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    installment = models.ForeignKey(SaleInstallment, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

class FixedCost(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='fixed_costs')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_day = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SpendingSettings(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE)
    reserve_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    updated_at = models.DateTimeField(auto_now=True)

class Transfer(models.Model):
    TRANSFER_TYPE_CHOICES = (
        ('pro_labore', 'Pró-Labore'),
        ('investment', 'Investimento'),
        ('withdrawal', 'Retirada'),
    )
    from_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transfers_out')
    to_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transfers_in')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPE_CHOICES)
    description = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

# Signals
from django.db.models.signals import post_save
from django.dispatch import receiver
from dateutil.relativedelta import relativedelta

@receiver(post_save, sender=Sale)
def create_sale_installments(sender, instance, created, **kwargs):
    if created and instance.installments_count > 0:
        installment_amount = instance.total_amount / instance.installments_count
        for i in range(instance.installments_count):
            due_date = instance.first_due_date + relativedelta(months=i)
            SaleInstallment.objects.create(
                sale=instance,
                installment_number=i + 1,
                amount=installment_amount,
                due_date=due_date,
                status='pending'
            )

@receiver(post_save, sender=Payment)
def update_installment_and_sale(sender, instance, created, **kwargs):
    if created:
        installment = instance.installment
        installment.status = 'paid'
        installment.paid_date = instance.payment_date
        installment.payment_method = instance.payment_method
        installment.save()

        sale = installment.sale
        sale.paid_amount += instance.amount
        sale.save() # This triggers Sale.save() which recalculates remaining_amount and status

@receiver(post_save, sender=Sale)
def update_customer_debt(sender, instance, created, **kwargs):
    customer = instance.customer
    from django.db.models import Sum
    total = customer.sales.aggregate(Sum('remaining_amount'))['remaining_amount__sum'] or 0
    if customer.total_debt != total:
        customer.total_debt = total
        customer.save(update_fields=['total_debt'])
