from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView
from .models import Transaction, Category, Customer, Sale, SaleInstallment, Payment, Transfer, FixedCost

class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    template_name = 'financial/transaction_form.html'
    fields = ['type', 'account', 'category', 'amount', 'date', 'payment_method', 'description']
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        
        # When a transaction is created, change the balance of the account
        response = super().form_valid(form)
        
        account = self.object.account
        if self.object.type == 'income':
            account.balance += self.object.amount
        elif self.object.type == 'expense':
            account.balance -= self.object.amount
        # Transfer type logic will be handled later
        account.save()
        
        return response

    def get_initial(self):
        initial = super().get_initial()
        # default to today
        from django.utils import timezone
        initial['date'] = timezone.now().date()
        return initial

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'financial/customer_list.html'
    context_object_name = 'customers'

    def get_queryset(self):
        # Customers for the user's active store
        store = self.request.user.stores.first()
        if store:
            return Customer.objects.filter(store=store)
        return Customer.objects.none()

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    template_name = 'financial/customer_form.html'
    fields = ['name', 'cpf', 'phone', 'address', 'notes']
    success_url = reverse_lazy('customer_list')

    def form_valid(self, form):
        store = self.request.user.stores.first()
        form.instance.store = store
        return super().form_valid(form)

class SaleCreateView(LoginRequiredMixin, CreateView):
    model = Sale
    template_name = 'financial/sale_form.html'
    fields = ['customer', 'total_amount', 'payment_type', 'installments_count', 'sale_date', 'first_due_date', 'notes']
    success_url = reverse_lazy('installment_list')

    def form_valid(self, form):
        form.instance.store = self.request.user.stores.first()
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        from django.utils import timezone
        today = timezone.now().date()
        initial['sale_date'] = today
        initial['first_due_date'] = today
        initial['installments_count'] = 1
        return initial

class InstallmentListView(LoginRequiredMixin, ListView):
    model = SaleInstallment
    template_name = 'financial/installment_list.html'
    context_object_name = 'installments'

    def get_queryset(self):
        store = self.request.user.stores.first()
        if store:
            # PRD: pending installments
            from django.utils import timezone
            import datetime
            limit_date = timezone.now().date() + datetime.timedelta(days=7)
            return SaleInstallment.objects.filter(
                sale__store=store, 
                status__in=['pending', 'overdue'],
                due_date__lte=limit_date
            ).order_by('due_date')
        return SaleInstallment.objects.none()

class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Payment
    template_name = 'financial/payment_form.html'
    fields = ['amount', 'payment_date', 'payment_method', 'notes']
    
    def get_success_url(self):
        return reverse_lazy('installment_list')

    def form_valid(self, form):
        from django.shortcuts import get_object_or_404
        installment = get_object_or_404(SaleInstallment, id=self.kwargs['pk'])
        form.instance.installment = installment
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.shortcuts import get_object_or_404
        context['installment'] = get_object_or_404(SaleInstallment, id=self.kwargs['pk'])
        return context

    def get_initial(self):
        initial = super().get_initial()
        from django.utils import timezone
        from django.shortcuts import get_object_or_404
        initial['payment_date'] = timezone.now().date()
        installment = get_object_or_404(SaleInstallment, id=self.kwargs['pk'])
        initial['amount'] = installment.amount
        return initial

class DebtorListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'financial/debtor_list.html'
    context_object_name = 'debtors'

    def get_queryset(self):
        store = self.request.user.stores.first()
        if store:
            return Customer.objects.filter(store=store, total_debt__gt=0).order_by('-total_debt')
        return Customer.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Sum
        context['total_owed'] = self.get_queryset().aggregate(Sum('total_debt'))['total_debt__sum'] or 0
        return context

class TransferCreateView(LoginRequiredMixin, CreateView):
    model = Transfer
    template_name = 'financial/transfer_form.html'
    fields = ['from_account', 'to_account', 'amount', 'transfer_type', 'description']
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # update balances
        transfer = self.object
        transfer.from_account.balance -= transfer.amount
        transfer.from_account.save()
        
        transfer.to_account.balance += transfer.amount
        transfer.to_account.save()
        
        return response

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # restrict accounts to current store
        store = self.request.user.stores.first()
        if store:
            from core.models import Account
            form.fields['from_account'].queryset = Account.objects.filter(store=store)
            form.fields['to_account'].queryset = Account.objects.filter(store=store)
        return form

class FixedCostListView(LoginRequiredMixin, ListView):
    model = FixedCost
    template_name = 'financial/fixedcost_list.html'
    context_object_name = 'fixed_costs'

    def get_queryset(self):
        store = self.request.user.stores.first()
        if store:
            from core.models import Account
            accounts = Account.objects.filter(store=store)
            return FixedCost.objects.filter(account__in=accounts)
        return FixedCost.objects.none()

class FixedCostCreateView(LoginRequiredMixin, CreateView):
    model = FixedCost
    template_name = 'financial/fixedcost_form.html'
    fields = ['account', 'category', 'name', 'amount', 'due_day']
    success_url = reverse_lazy('fixedcost_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        store = self.request.user.stores.first()
        if store:
            from core.models import Account
            form.fields['account'].queryset = Account.objects.filter(store=store)
            # Only expense categories
            form.fields['category'].queryset = Category.objects.filter(type='expense')
        return form
