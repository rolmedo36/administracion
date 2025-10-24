from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'codigo', 'nombre', 'nombre_comercial', 'tipo_cliente',
            'rfc', 'curp', 'regimen_fiscal', 'uso_cfdi',
            'email', 'telefono', 'telefono_movil', 'contacto_nombre',
            'calle', 'colonia', 'ciudad', 'estado', 'pais', 'codigo_postal',
            'limite_credito', 'dias_credito', 'descuento', 'moneda', 'clasificacion',
            'activo'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_comercial': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_cliente': forms.Select(attrs={'class': 'form-control'}),
            'rfc': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '13'}),
            'curp': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '18'}),
            'regimen_fiscal': forms.Select(attrs={'class': 'form-control'}),
            'uso_cfdi': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_movil': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'calle': forms.TextInput(attrs={'class': 'form-control'}),
            'colonia': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'}),
            'limite_credito': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dias_credito': forms.NumberInput(attrs={'class': 'form-control'}),
            'descuento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'moneda': forms.Select(attrs={'class': 'form-control'}),
            'clasificacion': forms.Select(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            # Generar código automáticamente
            last_cliente = Cliente.objects.order_by('-id').first()
            next_id = (last_cliente.id + 1) if last_cliente else 1
            self.fields['codigo'].initial = f"CLI-{next_id:04d}"
