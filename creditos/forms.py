# creditos/forms.py
from django import forms
from .models import CreditoProveedor, PagoCredito
from compras.models import Proveedor


class CreditoProveedorForm(forms.ModelForm):
    class Meta:
        model = CreditoProveedor
        fields = [
            'proveedor', 'monto_original', 'tasa_interes', 'fecha_desembolso',
            'fecha_inicio_pagos', 'frecuencia_pagos', 'num_cuotas',
            'metodo_calculo', 'descripcion', 'referencia'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'fecha_desembolso': forms.DateInput(attrs={'type': 'date'}),
            'fecha_inicio_pagos': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True)
        # Generar referencia automáticamente
        if not self.instance.pk:
            last_credito = CreditoProveedor.objects.order_by('-id').first()
            next_id = (last_credito.id + 1) if last_credito else 1
            self.fields['referencia'].initial = f"CR-{next_id:04d}"

    def clean(self):
        cleaned_data = super().clean()
        fecha_desembolso = cleaned_data.get('fecha_desembolso')
        fecha_inicio_pagos = cleaned_data.get('fecha_inicio_pagos')

        if fecha_desembolso and fecha_inicio_pagos:
            if fecha_inicio_pagos < fecha_desembolso:
                raise forms.ValidationError(
                    "La fecha de inicio de pagos no puede ser anterior a la fecha de desembolso.")

        return cleaned_data

class PagoCreditoForm(forms.ModelForm):
    class Meta:
        model = PagoCredito
        fields = ['monto_pagado', 'fecha_pago', 'referencia_pago']
        widgets = {
            'monto_pagado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_pago': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'referencia_pago': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Transferencia, Cheque #123'}),
        }

    def __init__(self, *args, **kwargs):
        self.amortizacion = kwargs.pop('amortizacion', None)
        super().__init__(*args, **kwargs)
        if self.amortizacion:
            # Establecer valor máximo (no puede pagar más que el monto total de la cuota)
            self.fields['monto_pagado'].widget.attrs['max'] = float(self.amortizacion.monto_total)
            self.fields['monto_pagado'].initial = self.amortizacion.monto_total

    def clean_monto_pagado(self):
        monto = self.cleaned_data['monto_pagado']
        if self.amortizacion and monto > self.amortizacion.monto_total:
            raise forms.ValidationError(f"El monto no puede ser mayor a ${self.amortizacion.monto_total}.")
        return monto
