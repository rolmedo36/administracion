# ventas/forms.py
from django import forms
from django.contrib.auth.models import User

from .models import CotizacionVenta, DetalleCotizacion, PedidoVenta, DetallePedido, FacturaVenta, DetalleFactura, CuentaPorCobrar, PagoCuentaPorCobrar, Vendedor

from clientes.models import Cliente
from materiales.models import Material
from flujocaja.models import CuentaBancaria

# === FORMULARIOS DE COTIZACIÓN ===

# ventas/forms.py

class CotizacionVentaForm(forms.ModelForm):
    class Meta:
        model = CotizacionVenta
        fields = ['cliente', 'dias_validez', 'vendedor', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'dias_validez': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'vendedor': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # Extraer el usuario del kwargs
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filtrar clientes y vendedores según el usuario
        if self.user and self.user.groups.filter(name='Vendedor').exists():
            try:
                vendedor = self.user.vendedor
                # Solo mostrar clientes asignados al vendedor
                self.fields['cliente'].queryset = Cliente.objects.filter(
                    activo=True,
                    vendedores_asignados=vendedor
                )
                # Vendedor no puede cambiar el vendedor (se asigna automáticamente)
                if 'vendedor' in self.fields:
                    del self.fields['vendedor']
            except Vendedor.DoesNotExist:
                self.fields['cliente'].queryset = Cliente.objects.none()
        else:
            # Administradores ven todos los clientes y pueden asignar vendedor
            self.fields['cliente'].queryset = Cliente.objects.filter(activo=True)
            self.fields['vendedor'].queryset = Vendedor.objects.filter(activo=True)

    def clean_cliente(self):
        cliente = self.cleaned_data.get('cliente')
        if (self.user and
                self.user.groups.filter(name='Vendedor').exists() and
                cliente):
            try:
                vendedor = self.user.vendedor
                if cliente not in vendedor.clientes_asignados.all():
                    raise forms.ValidationError("No tiene permisos para este cliente.")
            except Vendedor.DoesNotExist:
                raise forms.ValidationError("Error de configuración de vendedor.")
        return cliente

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
        fields = ['cliente', 'cotizacion', 'vendedor', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'cotizacion': forms.Select(attrs={'class': 'form-control'}),
            'vendedor': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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
        fields = ['cliente', 'pedido', 'folio', 'fecha', 'vendedor', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'pedido': forms.Select(attrs={'class': 'form-control'}),
            'folio': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vendedor': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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

class VendedorForm(forms.ModelForm):
    # Campos del usuario
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Nombre de usuario"
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Nombre"
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Apellidos"
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Contraseña",
        required=False
    )

    class Meta:
        model = Vendedor
        fields = ['codigo', 'telefono', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Edición - prellenar campos del usuario
            self.fields['username'].initial = self.instance.usuario.username
            self.fields['first_name'].initial = self.instance.usuario.first_name
            self.fields['last_name'].initial = self.instance.usuario.last_name
            self.fields['email'].initial = self.instance.usuario.email
            self.fields['password'].required = False
        else:
            # Creación - contraseña requerida
            self.fields['password'].required = True

    def save(self, commit=True):
        vendedor = super().save(commit=False)

        if not vendedor.pk:
            # Crear nuevo usuario
            usuario = User.objects.create_user(
                username=self.cleaned_data['username'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password']
            )
            vendedor.usuario = usuario
            vendedor.nombre_completo = f"{self.cleaned_data['first_name']} {self.cleaned_data['last_name']}".strip()
            vendedor.email = self.cleaned_data['email']
        else:
            # Actualizar usuario existente
            usuario = vendedor.usuario
            usuario.username = self.cleaned_data['username']
            usuario.first_name = self.cleaned_data['first_name']
            usuario.last_name = self.cleaned_data['last_name']
            usuario.email = self.cleaned_data['email']
            if self.cleaned_data['password']:
                usuario.set_password(self.cleaned_data['password'])
            usuario.save()

            vendedor.nombre_completo = f"{self.cleaned_data['first_name']} {self.cleaned_data['last_name']}".strip()
            vendedor.email = self.cleaned_data['email']

        if commit:
            vendedor.save()
        return vendedor
