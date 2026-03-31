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

            from financial.models import Customer
            context['total_customers'] = Customer.objects.filter(store=store).count()
            context['total_pending'] = Customer.objects.filter(store=store).aggregate(Sum('total_debt'))['total_debt__sum'] or Decimal('0.00')

            # F003: Inadimplentes Dashboard list
            context['top_debtors'] = Customer.objects.filter(store=store, total_debt__gt=0).order_by('-total_debt')

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

    return render(request, 'onboarding.html')

import os
from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def subscription_view(request):
    return render(request, 'subscription.html')

@login_required
def create_checkout(request, plan):
    if plan not in ['basic', 'pro']:
        return redirect('subscription')
    
    price = 2900 if plan == 'basic' else 4900
    plan_name = "Plano Básico HMF" if plan == 'basic' else "Plano PRO HMF"
    
    try:
        from abacatepay import AbacatePay
        abacate = AbacatePay(os.environ.get('ABACATEPAY_API_KEY'))
        
        # Build completion URL based on current host
        host = request.get_host()
        scheme = request.scheme
        base_url = f"{scheme}://{host}"
        
        # AbacatePay SDK Pydantic regex rejects 127.0.0.1 and localhost.
        if '127.0.0.1' in host or 'localhost' in host:
            base_url = "https://hmfinancas-app.com"
        
        response = abacate.billing.create(
            frequency="ONE_TIME", # "RECURRING" SDK support might vary, using ONE_TIME for MVP
            methods=["PIX"],
            products=[{
                "name": plan_name,
                "quantity": 1,
                "price": price
            }],
            customer={
                "name": request.user.username or request.user.email.split('@')[0],
                "email": request.user.email
            },
            return_url=base_url + reverse('dashboard'),
            completion_url=base_url + reverse('dashboard') + "?upgraded=true"
        )
        
        # Save intent ID to user if needed, but for MVP we match email in webhook
        request.user.abacatepay_subscription_id = response.data.id
        request.user.save()
        
        return redirect(response.data.url)
    except Exception as e:
        print(f"AbacatePay error: {e}")
        from django.contrib import messages
        messages.error(request, "Erro ao gerar cobrança. Tente novamente.")
        return redirect('subscription')

@csrf_exempt
def webhook_abacatepay(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            # Simplest webhook handling for MVP
            event = payload.get('event')
            data = payload.get('data', {})
            
            if event == 'billing.paid':
                billing_id = data.get('id')
                # Find user by billing ID or email
                from core.models import User
                user = User.objects.filter(abacatepay_subscription_id=billing_id).first()
                if not user:
                    customer_email = data.get('customer', {}).get('email')
                    if customer_email:
                        user = User.objects.filter(email=customer_email).first()
                
                if user:
                    amount = data.get('amount', 0)
                    user.plan = 'pro' if amount > 3000 else 'basic'
                    user.plan_status = 'active'
                    user.save()
                    
            return HttpResponse(status=200)
        except Exception as e:
            return HttpResponse(status=400)
    return HttpResponse(status=405)
