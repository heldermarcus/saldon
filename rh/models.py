from django.db import models
from core.models import Store

class Employee(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='employees', verbose_name="Loja")
    name = models.CharField(max_length=200, verbose_name="Nome do Funcionário")
    cpf = models.CharField(max_length=14, null=True, blank=True, verbose_name="CPF")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefone")
    role = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cargo")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
