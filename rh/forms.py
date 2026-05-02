from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'cpf', 'phone', 'role', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00', 'data-mask': '000.000.000-00'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000', 'data-mask': '(00) 00000-0000'}),
            'role': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Vendedor, Caixa'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
