import re
from decimal import Decimal
from django.utils import timezone
from core.models import Account
from financial.models import Sale, Transaction, Category, Customer

def process_whatsapp_message(message):
    """
    Processa uma mensagem recebida do WhatsApp, identifica a intenção
    e executa a ação financeira.
    """
    if not message.text:
        return None

    text = message.text.lower().strip()
    store = message.integration.store
    user = store.user

    # Regex atualizada para capturar:
    # 1. Ação: vendi e recebi, vendi, recebi, gastei
    # 2. Valor: 50, 50.00, 50,00
    # 3. Pessoa (opcional): para Joao, de Maria, com Fornecedor X
    pattern = r'^(vendi e recebi|vendi|recebi|gastei)\s+(?:r\$)?\s*(\d+(?:[.,]\d{1,2})?)(?:\s+(?:para|de|com|da|do)\s+(.+))?'
    match = re.search(pattern, text)

    if not match:
        message.processed = True
        message.intent = 'unknown'
        message.save()
        return (
            "🤖 Olá! Eu sou o robô do Saldon. Veja como falar comigo:\n\n"
            "💰 *Vendi e recebi 50* (Venda paga na hora)\n"
            "📝 *Vendi 50 para Joao* (Venda fiado/pendente)\n"
            "📥 *Recebi 50 do Joao* (Pagamento de dívida)\n"
            "💸 *Gastei 20 com Luz* (Despesa)"
        )

    action = match.group(1) # vendi, vendi e recebi, recebi, gastei
    amount_str = match.group(2).replace(',', '.')
    person_name = match.group(3)
    
    try:
        amount = Decimal(amount_str)
    except:
        return "❌ Desculpe, não consegui entender o valor numérico."

    # Encontrar a conta principal da loja
    account = Account.objects.filter(store=store).first()
    if not account:
        return "❌ Erro: Nenhuma conta bancária/caixa cadastrada para esta loja."

    # Lógica de Cliente
    customer = None
    if person_name:
        person_name = person_name.strip().title()
        # Busca cliente existente com nome parecido ou cria um novo
        customer = Customer.objects.filter(store=store, name__icontains=person_name).first()
        if not customer:
            customer = Customer.objects.create(store=store, name=person_name)

    response_text = ""
    today = timezone.now().date()

    if action == 'vendi':
        # Só Vendeu (Fiado/Pendente). Não entra dinheiro no caixa.
        sale = Sale.objects.create(
            store=store,
            customer=customer,
            total_amount=amount,
            paid_amount=0,
            installments_count=1,
            payment_type='promissory', # Assumindo promissória/fiado
            status='pending',
            sale_date=today,
            first_due_date=today, # Pode ser ajustado depois
            notes=f"Lançado via WhatsApp: {message.text}"
        )
        message.intent = 'sale_pending'
        person_info = f" para {customer.name}" if customer else ""
        response_text = f"📝 Caderneta anotada! Venda pendente de R$ {amount:.2f}{person_info} registrada. O dinheiro ainda NÃO entrou no caixa."

    elif action == 'vendi e recebi':
        # Vendeu e já Recebeu na hora. Vai pra Vendas e pro Caixa.
        category, _ = Category.objects.get_or_create(
            user=user, name="Vendas via WhatsApp", 
            defaults={'type': 'income', 'is_default': False}
        )

        sale = Sale.objects.create(
            store=store,
            customer=customer,
            total_amount=amount,
            paid_amount=amount,
            installments_count=1,
            payment_type='pix',
            status='paid',
            sale_date=today,
            first_due_date=today,
            notes=f"Vendido e recebido via WhatsApp: {message.text}"
        )

        Transaction.objects.create(
            account=account,
            category=category,
            type='income',
            amount=amount,
            description=f"Venda WhatsApp" + (f" ({customer.name})" if customer else ""),
            date=today,
            payment_method='pix',
            created_by=user,
            sale=sale
        )

        message.intent = 'sale_paid'
        person_info = f" de {customer.name}" if customer else ""
        response_text = f"✅ Sucesso! Venda de R$ {amount:.2f}{person_info} registrada e o dinheiro já entrou no fluxo de caixa!"

    elif action == 'recebi':
        # Apenas Recebeu (Entrada). Sem criar uma nova "Venda" no dashboard.
        # Útil para quando o cliente está pagando uma dívida antiga ou outra entrada.
        category, _ = Category.objects.get_or_create(
            user=user, name="Recebimentos Diversos", 
            defaults={'type': 'income', 'is_default': False}
        )

        Transaction.objects.create(
            account=account,
            category=category,
            type='income',
            amount=amount,
            description=f"Recebimento WhatsApp" + (f" ({customer.name})" if customer else ""),
            date=today,
            payment_method='pix',
            created_by=user
        )
        
        # (Opcional Futuro: Achar vendas 'pending' do cliente e abater o valor automaticamente)

        message.intent = 'income'
        person_info = f" do(a) {customer.name}" if customer else ""
        response_text = f"📥 Entrada de R$ {amount:.2f}{person_info} registrada no seu caixa!"

    elif action == 'gastei':
        # Despesa
        category, _ = Category.objects.get_or_create(
            user=user, name="Despesas Gerais (WhatsApp)", 
            defaults={'type': 'expense', 'is_default': False}
        )

        desc = f"Despesa WhatsApp" + (f": {person_name}" if person_name else "")

        Transaction.objects.create(
            account=account,
            category=category,
            type='expense',
            amount=amount,
            description=desc,
            date=today,
            payment_method='pix',
            created_by=user
        )

        message.intent = 'expense'
        person_info = f" com {person_name}" if person_name else ""
        response_text = f"💸 Despesa de R$ {amount:.2f}{person_info} registrada!"

    message.processed = True
    message.save()

    print(f"[WHATSAPP BOT SEND] -> {response_text}")
    return response_text
