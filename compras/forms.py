from django import forms
from django.forms import inlineformset_factory
from .models import Proveedor, OrdenCompra, DetalleOrdenCompra, CuentaPorPagar, PagoCuentaPorPagar
from materiales.models import Almacen

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'identificacion', 'telefono', 'email', 'direccion', 'activo']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 2}),
        }

# Orden de compra
class OrdenCompraForm(forms.ModelForm):
    class Meta:
        model = OrdenCompra
        fields = ['numero', 'proveedor', 'estado']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'proveedor': forms.Select(attrs={'class': 'd-none'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            # Nueva orden: solo permite "borrador"
            self.fields['estado'].choices = [('borrador', 'Borrador')]
            last_oc = OrdenCompra.objects.order_by('-id').first()
            next_id = (last_oc.id + 1) if last_oc else 1
            self.fields['numero'].initial = f"OC-{next_id:04d}"
        else:
            # Edición: filtra estados permitidos
            if self.instance.estado == 'borrador':
                self.fields['estado'].choices = [
                    ('borrador', 'Borrador'),
                    ('confirmada', 'Confirmada'),
                    ('cancelada', 'Cancelada'),
                ]
            elif self.instance.estado == 'confirmada':
                self.fields['estado'].choices = [
                    ('confirmada', 'Confirmada'),
                    ('cancelada', 'Cancelada'),
                ]
            else:
                # recibida o cancelada: no se puede cambiar
                self.fields['estado'].disabled = True

        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True)

class DetalleOrdenCompraForm(forms.ModelForm):
    """
    Formulario para cada línea del detalle de la orden.
    El campo 'material' se llenará mediante modal, pero debe estar en 'fields'
    para que el formset lo procese correctamente.
    """
    class Meta:
        model = DetalleOrdenCompra
        fields = ['material', 'cantidad', 'precio_unitario', 'aplica_iva', 'precio_con_iva']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-control d-none'}),  # oculto, pero necesario
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'aplica_iva': forms.HiddenInput(),
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad and cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor a cero.")
        return cantidad

    def clean_precio_unitario(self):
        precio = self.cleaned_data.get('precio_unitario')
        if precio and precio <= 0:
            raise forms.ValidationError("El precio unitario debe ser mayor a cero.")
        return precio

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que precio_con_iva no sea requerido en el formulario
        self.fields['precio_con_iva'].required = False

    def clean_precio_con_iva(self):
        # El valor se calculará en el modelo, no en el formulario
        return self.cleaned_data.get('precio_con_iva') or 0

# Formset para los detalles de la orden
DetalleOrdenFormSet = inlineformset_factory(
    OrdenCompra,
    DetalleOrdenCompra,
    form=DetalleOrdenCompraForm,
    extra=1,
    max_num=100,
    can_delete=True,
    can_delete_extra=True
)

class RecepcionOrdenForm(forms.Form):
    referencia = forms.CharField(
        label="Factura o Referencia",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    fecha_vencimiento = forms.DateField(
        label="Fecha de Vencimiento",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.filter(activo=True),
        label="Almacén de Recepción",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Seleccione un almacén"
    )

# CXP
class PagoCuentaPorPagarForm(forms.ModelForm):
    class Meta:
        model = PagoCuentaPorPagar
        fields = ['monto', 'fecha_pago', 'referencia']
        widgets = {
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'fecha_pago': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'referencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Transferencia, Cheque #123'}),
        }

    def __init__(self, *args, **kwargs):
        self.cxp = kwargs.pop('cxp', None)
        super().__init__(*args, **kwargs)

    def clean_monto(self):
        monto = self.cleaned_data['monto']
        if self.cxp and monto > self.cxp.saldo_pendiente:
            raise forms.ValidationError(
                f"El monto no puede ser mayor al saldo pendiente (${self.cxp.saldo_pendiente})."
            )
        return monto
