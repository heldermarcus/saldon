from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from core.models import Store, Account
from financial.models import Category

class LandingPageView(TemplateView):
    template_name = 'landing.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not getattr(request.user, 'onboarding_completed', False):
            return redirect('onboarding')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = self.request.user.stores.first()
        if store:
            pf_acc = store.accounts.filter(account_type='PF').first()
            pj_acc = store.accounts.filter(account_type='PJ').first()
            context['pf_account'] = pf_acc
            context['pj_account'] = pj_acc
            
            # F003 / F010: "Quanto posso gastar hoje?"
            can_spend_today = 0
            if pj_acc:
                from financial.models import FixedCost, SpendingSettings
                from django.db.models import Sum
                from decimal import Decimal

                fixed_costs_sum = FixedCost.objects.filter(account=pj_acc, is_active=True).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
                
                settings, _ = SpendingSettings.objects.get_or_create(account=pj_acc, defaults={'reserve_percentage': 10})
                reserve_factor = settings.reserve_percentage / Decimal('100.00')
                
                # Formula: Saldo PJ - (Soma Custos Fixos)
                # O restante sofre desconto da Reserva %
                available_after_fixed = pj_acc.balance - fixed_costs_sum
                
                if available_after_fixed > 0:
                    reserve_amount = available_after_fixed * reserve_factor
                    can_spend_today = available_after_fixed - reserve_amount
                    
            context['can_spend_today'] = max(Decimal('0.00'), can_spend_today)

            # F003: Inadimplentes Dashboard list
            from financial.models import Customer
            context['top_debtors'] = Customer.objects.filter(store=store, total_debt__gt=0).order_by('-total_debt')[:5]

        return context

@login_required
def onboarding_view(request):
    if request.user.onboarding_completed:
        return redirect('dashboard')

    if request.method == 'POST':
        store_name = request.POST.get('store_name')
        if store_name:
            store, _ = Store.objects.get_or_create(user=request.user, name=store_name)
            
            # Create PF and PJ accounts
            Account.objects.get_or_create(store=store, account_type='PF', defaults={'name': f'Pessoal {request.user.username}'})
            Account.objects.get_or_create(store=store, account_type='PJ', defaults={'name': 'Caixa Loja'})

            # Create default categories if they don't exist
            Category.objects.get_or_create(name='Vendas', type='income', account_type='PJ', is_default=True)
            Category.objects.get_or_create(name='Salário/Pró-labore', type='income', account_type='PF', is_default=True)
            Category.objects.get_or_create(name='Fornecedor', type='expense', account_type='PJ', is_default=True)
            Category.objects.get_or_create(name='Aluguel', type='expense', account_type='PJ', is_fixed_cost=True, is_default=True)
            Category.objects.get_or_create(name='Luz/Água', type='expense', account_type='PJ', is_fixed_cost=True, is_default=True)
            Category.objects.get_or_create(name='Funcionário', type='expense', account_type='PJ', is_fixed_cost=True, is_default=True)
            Category.objects.get_or_create(name='Pessoal', type='expense', account_type='PF', is_default=True)

            request.user.onboarding_completed = True
            request.user.save()

            return redirect('dashboard')

    return render(request, 'onboarding.html')
