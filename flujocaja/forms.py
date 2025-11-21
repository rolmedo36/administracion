from django import forms
from .models import Banco, CuentaBancaria, MovimientoBancario

class BancoForm(forms.ModelForm):
    class Meta:
        model = Banco
        fields = ['nombre', 'codigo', 'pais', 'swift', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
            'swift': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CuentaBancariaForm(forms.ModelForm):
    class Meta:
        model = CuentaBancaria
        fields = ['banco', 'numero_cuenta', 'clabe', 'tipo_cuenta', 'moneda', 'descripcion', 'activo']
        widgets = {
            'banco': forms.Select(attrs={'class': 'form-control'}),
            'numero_cuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'clabe': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_cuenta': forms.Select(attrs={'class': 'form-control'}),
            'moneda': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['banco'].queryset = Banco.objects.filter(activo=True)

# MOVIMIENTOS CAJA

class MovimientoBancarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoBancario
        fields = [
            'cuenta_bancaria', 'tipo_movimiento', 'monto',
            'fecha', 'descripcion', 'referencia',
            'tipo_documento', 'documento_numero'
        ]
        widgets = {
            'cuenta_bancaria': forms.Select(attrs={'class': 'form-control'}),
            'tipo_movimiento': forms.Select(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del movimiento...'
            }),
            'referencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Transferencia, Cheque #123'
            }),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'documento_numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Folio, OC, Factura...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cuenta_bancaria'].queryset = CuentaBancaria.objects.filter(activo=True)
