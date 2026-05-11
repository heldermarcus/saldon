from django.db import models
from core.models import Store

class WhatsAppIntegration(models.Model):
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='whatsapp_integration')
    instance_name = models.CharField(max_length=100, unique=True, help_text="Nome da instância na API do WhatsApp (ex: Evolution API)")
    instance_key = models.CharField(max_length=255, blank=True, help_text="Chave de segurança da instância")
    status = models.CharField(max_length=50, default='DISCONNECTED') # DISCONNECTED, CONNECTING, CONNECTED, QRCODE
    qr_code_base64 = models.TextField(blank=True, null=True, help_text="Último QR Code gerado para conectar")
    number = models.CharField(max_length=50, blank=True, null=True, help_text="Número de telefone conectado")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"WhatsApp: {self.store.name} ({self.status})"

class WhatsAppMessage(models.Model):
    integration = models.ForeignKey(WhatsAppIntegration, on_delete=models.CASCADE, related_name='messages')
    remote_jid = models.CharField(max_length=100, help_text="ID do contato (número@s.whatsapp.net)")
    message_id = models.CharField(max_length=100, unique=True)
    text = models.TextField(blank=True, null=True)
    is_from_me = models.BooleanField(default=False)
    timestamp = models.DateTimeField()
    
    # Processamento de IA / Intent
    processed = models.BooleanField(default=False)
    intent = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Msg {self.id} - {self.remote_jid}"
