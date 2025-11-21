# ventas/forms.py
from django import forms
from .models import CotizacionVenta, DetalleCotizacion, PedidoVenta, DetallePedido, FacturaVenta, DetalleFactura, CuentaPorCobrar, PagoCuentaPorCobrar

from clientes.models import Cliente
from materiales.models import Material
from flujocaja.models import CuentaBancaria

# === FORMULARIOS DE COTIZACIÓN ===

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
                'max': '100',
                'value': '0'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['material'].queryset = Material.objects.filter(activo=True, es_inventariable=True)

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
    max_num=100
)

# === FORMULARIOS DE PEDIDOS ===

class PedidoVentaForm(forms.ModelForm):
    class Meta:
        model = PedidoVenta
        fields = ['cliente', 'cotizacion']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'cotizacion': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(activo=True)
        self.fields['cotizacion'].queryset = CotizacionVenta.objects.filter(estado='aceptada')

class DetallePedidoForm(forms.ModelForm):
    class Meta:
        model = DetallePedido
        fields = ['material', 'cantidad_solicitada', 'precio_unitario', 'descuento']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-control'}),
            'cantidad_solicitada': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descuento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['material'].queryset = Material.objects.filter(activo=True, es_inventariable=True)

    def clean_descuento(self):
        descuento = self.cleaned_data.get('descuento')
        if descuento is None or descuento == '':
            return 0
        if descuento < 0:
            return 0
        if descuento > 100:
            raise forms.ValidationError("El descuento no puede ser mayor a 100%")
        return descuento

DetallePedidoFormSet = forms.inlineformset_factory(
    PedidoVenta,
    DetallePedido,
    form=DetallePedidoForm,
    extra=0,
    can_delete=True,
    max_num=100
)

# FACTURAS

class FacturaVentaForm(forms.ModelForm):
    class Meta:
        model = FacturaVenta
        fields = ['cliente', 'pedido', 'folio', 'fecha']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'pedido': forms.Select(attrs={'class': 'form-control'}),
            'folio': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(activo=True)
        self.fields['pedido'].queryset = PedidoVenta.objects.filter(estado='completo')

class DetalleFacturaForm(forms.ModelForm):
    class Meta:
        model = DetalleFactura
        fields = ['material', 'cantidad', 'precio_unitario', 'descuento', 'iva_porcentaje']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control cantidad-input',
                'step': '0.01',
                'min': '0.01'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control precio-unitario-input',
                'step': '0.01',
                'min': '0.01'
            }),
            'descuento': forms.NumberInput(attrs={
                'class': 'form-control descuento-input',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'iva_porcentaje': forms.NumberInput(attrs={
                'class': 'form-control iva-porcentaje-input',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['material'].queryset = Material.objects.filter(activo=True, es_inventariable=True)

DetalleFacturaFormSet = forms.inlineformset_factory(
    FacturaVenta,
    DetalleFactura,
    form=DetalleFacturaForm,
    extra=0,
    can_delete=True,
    max_num=100
)

class PagoCuentaPorCobrarForm(forms.ModelForm):
    cuenta_bancaria = forms.ModelChoiceField(
        queryset=CuentaBancaria.objects.filter(activo=True),
        label="Cuenta Bancaria",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = PagoCuentaPorCobrar
        fields = ['monto', 'fecha_pago', 'referencia', 'cuenta_bancaria']
        widgets = {
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'fecha_pago': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'referencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Transferencia, Cheque #123'
            }),
        }
