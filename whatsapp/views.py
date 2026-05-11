import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import WhatsAppIntegration, WhatsAppMessage
from core.models import Store
from datetime import datetime

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_whatsapp_status(request, store_id):
    """
    Retorna o status atual da integração do WhatsApp para a loja selecionada.
    """
    try:
        store = Store.objects.get(id=store_id, user=request.user)
    except Store.DoesNotExist:
        return Response({"error": "Loja não encontrada ou não pertence a este usuário."}, status=404)

    integration, created = WhatsAppIntegration.objects.get_or_create(
        store=store,
        defaults={'instance_name': f"store_{store.id}_wpp"}
    )
    
    return Response({
        "status": integration.status,
        "instance_name": integration.instance_name,
        "number": integration.number,
        "qr_code_base64": integration.qr_code_base64 if integration.status == 'QRCODE' else None,
        "updated_at": integration.updated_at
    })

@csrf_exempt
def whatsapp_webhook(request, instance_name):
    """
    Endpoint para receber Webhooks de serviços como Evolution API, Z-API, WPPConnect, etc.
    Espera receber requisições POST com payloads em JSON.
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Identificar a integração baseada na URL
    try:
        integration = WhatsAppIntegration.objects.get(instance_name=instance_name)
    except WhatsAppIntegration.DoesNotExist:
        return JsonResponse({"error": "Instance not found"}, status=404)

    # Estrutura básica: Exemplo de tratamento para Evolution API (message.upsert ou connection.update)
    event_type = payload.get('event', '')

    if event_type == 'connection.update':
        data = payload.get('data', {})
        state = data.get('state', '')
        if state == 'open':
            integration.status = 'CONNECTED'
            integration.qr_code_base64 = None
        elif state == 'close':
            integration.status = 'DISCONNECTED'
        elif state == 'connecting':
            integration.status = 'CONNECTING'
        
        # O Base64 do QR code se vier na atualização
        if 'qrcode' in data and data['qrcode']:
            integration.status = 'QRCODE'
            integration.qr_code_base64 = data['qrcode']
            
        integration.save()
        return JsonResponse({"status": "Connection updated"})

    elif event_type == 'messages.upsert':
        # Aqui é onde recebemos a mensagem do cliente ou do próprio dono
        messages = payload.get('data', {}).get('messages', [])
        for msg in messages:
            # Pula mensagens do sistema ou status
            if msg.get('key', {}).get('remoteJid') == 'status@broadcast':
                continue

            remote_jid = msg.get('key', {}).get('remoteJid', '')
            message_id = msg.get('key', {}).get('id', '')
            is_from_me = msg.get('key', {}).get('fromMe', False)
            
            # Extrair texto (depende do tipo de mensagem: text, conversation, extendedTextMessage)
            text = ""
            msg_content = msg.get('message', {})
            if 'conversation' in msg_content:
                text = msg_content['conversation']
            elif 'extendedTextMessage' in msg_content:
                text = msg_content['extendedTextMessage'].get('text', '')
            
            # Timestamp
            ts = msg.get('messageTimestamp')
            timestamp = datetime.fromtimestamp(int(ts)) if ts else datetime.now()

            # Salva no banco de dados para a IA ou Fluxo de caixa processar depois
            msg_obj = WhatsAppMessage.objects.create(
                integration=integration,
                remote_jid=remote_jid,
                message_id=message_id,
                text=text,
                is_from_me=is_from_me,
                timestamp=timestamp
            )

            # Só processa se não fomos nós que enviamos
            if not is_from_me:
                from .processor import process_whatsapp_message
                response_text = process_whatsapp_message(msg_obj)
                
                if response_text:
                    # Aqui faríamos o POST real para a API Evolution para enviar a resposta
                    pass

        return JsonResponse({"status": "Messages processed"})

    return JsonResponse({"status": "Ignored event type"})
