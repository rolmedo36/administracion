from django import forms
from .models import CotizacionVenta, DetalleCotizacion
from clientes.models import Cliente
from materiales.models import Material

class CotizacionVentaForm(forms.ModelForm):
    class Meta:
        model = CotizacionVenta
        fields = ['cliente', 'dias_validez']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'dias_validez': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(activo=True)

class DetalleCotizacionForm(forms.ModelForm):
    class Meta:
        model = DetalleCotizacion
        fields = ['material', 'cantidad', 'precio_unitario', 'descuento']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-control material-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control cantidad-input', 'step': '0.01', 'min': '0.01'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control precio-input', 'step': '0.01', 'min': '0.01'}),
            'descuento': forms.NumberInput(attrs={
                'class': 'form-control descuento-input',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Forzar valor por defecto en todos los casos
        self.fields['descuento'].initial = 0
        self.fields['descuento'].required = False

    def clean_descuento(self):
        descuento = self.cleaned_data.get('descuento')
        if descuento is None or descuento == '':
            return 0
        if descuento < 0:
            return 0
        if descuento > 100:
            raise forms.ValidationError("El descuento no puede ser mayor a 100%")
        return descuento

DetalleCotizacionFormSet = forms.inlineformset_factory(
    CotizacionVenta,
    DetalleCotizacion,
    form=DetalleCotizacionForm,
    extra=0,
    can_delete=True,
    max_num=100  # Permite hasta 100 líneas
)