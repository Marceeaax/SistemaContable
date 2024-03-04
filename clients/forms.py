from django import forms
from .models import PersonaFisica, PersonaJuridica
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class PersonaFisicaForm(forms.ModelForm):
    nombre = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Nombre'}), label='')
    apellido = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Apellido'}), label='')
    cedula = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Cédula'}), label='')
    contrasena = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Contraseña (Marangatu)'}), label='')
    telefono = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Teléfono'}), label='')
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Email'}), label='')
    fecha_nacimiento = forms.DateField(widget=forms.TextInput(attrs={'placeholder': 'Fecha de nacimiento'}), label='')
    direccion = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Dirección'}), label='')
    
    def clean_cedula(self):
        cedula = self.cleaned_data.get("cedula")
        if PersonaFisica.objects.filter(cedula=cedula).exists():
            raise ValidationError(_("Esta cédula ya está registrada."))
        return cedula
    
    class Meta:
        model = PersonaFisica
        fields = ['nombre', 'apellido', 'cedula', 'contrasena', 'telefono', 'email', 'fecha_nacimiento', 'direccion']

class PersonaJuridicaForm(forms.ModelForm):
    razon_social = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Razón social'}), label='')
    ruc = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'RUC'}), label='')
    direccion_fiscal = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Dirección fiscal'}), label='')
    representante_legal = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Representante legal'}), label='')
    telefono = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Telefono'}), label='')
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Email'}), label='')

    class Meta:
        model = PersonaJuridica
        fields = ['razon_social', 'ruc', 'direccion_fiscal', 'representante_legal', 'telefono', 'email']
