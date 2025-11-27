from django import forms
from .models import Empresa

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'razon_social', 'nombre_comercial', 'rfc',
            'domicilio_calle', 'domicilio_numero', 'domicilio_colonia',
            'domicilio_ciudad', 'domicilio_estado', 'domicilio_pais',
            'domicilio_cp', 'telefono', 'email', 'logo'
        ]
        widgets = {
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_comercial': forms.TextInput(attrs={'class': 'form-control'}),
            'rfc': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '13'}),
            'domicilio_calle': forms.TextInput(attrs={'class': 'form-control'}),
            'domicilio_numero': forms.TextInput(attrs={'class': 'form-control'}),
            'domicilio_colonia': forms.TextInput(attrs={'class': 'form-control'}),
            'domicilio_ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'domicilio_estado': forms.TextInput(attrs={'class': 'form-control'}),
            'domicilio_pais': forms.TextInput(attrs={'class': 'form-control'}),
            'domicilio_cp': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }