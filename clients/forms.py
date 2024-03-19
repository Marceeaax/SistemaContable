from django import forms
from .models import PersonaFisica, PersonaJuridica
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class PersonaFisicaForm(forms.ModelForm):
    nombre = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Nombre'}), label='')
    apellido = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Apellido'}), label='')
    ruc = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'RUC'}), label='')
    contrasena = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Contraseña (Marangatu)'}), label='')
    telefono = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Teléfono'}), label='', required=False)
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Email'}), label='', required=False)
    fecha_nacimiento = forms.DateField(widget=forms.TextInput(attrs={'placeholder': 'Fecha de nacimiento'}), label='', required=False)
    direccion = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Dirección'}), label='', required=False)
    
    def calcular_cedula(self):
        ruc = self.cleaned_data.get("ruc")
        cedula = ruc[:-2]
        return cedula  #probablemente esta funcion no sirve
    
    def clean_ruc(self):
        ruc = self.cleaned_data.get("ruc")
        if PersonaFisica.objects.filter(ruc=ruc).exists():
            raise ValidationError(_("Este RUC ya existe."))
        return ruc
    
    class Meta:
        model = PersonaFisica
        fields = ['nombre', 'apellido', 'ruc', 'contrasena', 'telefono', 'email', 'fecha_nacimiento', 'direccion']

class PersonaJuridicaForm(forms.ModelForm):
    razon_social = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Razón social'}), label='')
    ruc = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'RUC'}), label='')
    direccion_fiscal = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Dirección fiscal'}), label='', required=False)
    representante_legal = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Representante legal'}), label='', required=False)
    telefono = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Telefono'}), label='', required=False)
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Email'}), label='', required=False)

    class Meta:
        model = PersonaJuridica
        fields = ['razon_social', 'ruc', 'direccion_fiscal', 'representante_legal', 'telefono', 'email']
