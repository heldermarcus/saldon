from django import forms
from .models import User, Store


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['name', 'cnpj', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'ex: Mercearia do João'}),
            'cnpj': forms.TextInput(attrs={'placeholder': '00.000.000/0000-00'}),
            'phone': forms.TextInput(attrs={'placeholder': '(00) 00000-0000'}),
            'address': forms.Textarea(attrs={'placeholder': 'Rua, número, bairro, cidade - UF', 'rows': 3}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'cpf']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Seu nome'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Sobrenome'}),
            'phone': forms.TextInput(attrs={'placeholder': '(00) 00000-0000'}),
            'cpf': forms.TextInput(attrs={'placeholder': '000.000.000-00'}),
        }
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
        }
