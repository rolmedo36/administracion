from django import forms
from .models import Material, CategoriaMaterial, Almacen, MovimientoAlmacen, DetalleMovimientoAlmacen

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = [
            'codigo', 'nombre', 'descripcion', 'categoria',
            'unidad_medida', 'precio_unitario', 'es_inventariable',
            'stock_actual', 'stock_minimo', 'activo', 'aplica_iva'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01'}),
            'stock_actual': forms.NumberInput(attrs={'step': '0.01'}),
            'stock_minimo': forms.NumberInput(attrs={'step': '0.01'}),
            'aplica_iva': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.instance.creado_por = user

    def clean(self):
        cleaned_data = super().clean()
        es_inventariable = cleaned_data.get('es_inventariable')
        stock_actual = cleaned_data.get('stock_actual')
        stock_minimo = cleaned_data.get('stock_minimo')

        if es_inventariable:
            if stock_actual is not None and stock_actual < 0:
                self.add_error('stock_actual', 'El stock actual no puede ser negativo.')
            if stock_minimo is not None and stock_minimo < 0:
                self.add_error('stock_minimo', 'El stock mínimo no puede ser negativo.')
        return cleaned_data

class CategoriaMaterialForm(forms.ModelForm):
    class Meta:
        model = CategoriaMaterial
        fields = ['nombre', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        # Validar unicidad insensible a mayúsculas/minúsculas
        if CategoriaMaterial.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe una categoría con este nombre.")
        return nombre

# Almacenes
class AlmacenForm(forms.ModelForm):
    class Meta:
        model = Almacen
        fields = ['codigo', 'nombre', 'descripcion', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'activo': forms.CheckboxInput(),
        }

# Movimiento de almacen

class MovimientoAlmacenForm(forms.ModelForm):
    class Meta:
        model = MovimientoAlmacen
        fields = ['almacen_origen', 'documento_referencia', 'notas']
        widgets = {
            'almacen_origen': forms.Select(attrs={'class': 'form-control'}),
            'documento_referencia': forms.TextInput(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        tipo = kwargs.pop('tipo', None)
        super().__init__(*args, **kwargs)

        if tipo == 'entrada':
            self.fields['almacen_destino'] = forms.ModelChoiceField(
                queryset=Almacen.objects.filter(activo=True),
                widget=forms.Select(attrs={'class': 'form-control'}),
                label="Almacén de Destino"
            )
        elif tipo == 'salida':
            self.fields['almacen_origen'] = forms.ModelChoiceField(
                queryset=Almacen.objects.filter(activo=True),
                widget=forms.Select(attrs={'class': 'form-control'}),
                label="Almacén de Origen"
            )
        elif tipo == 'transferencia':
            self.fields['almacen_origen'] = forms.ModelChoiceField(
                queryset=Almacen.objects.filter(activo=True),
                widget=forms.Select(attrs={'class': 'form-control'}),
                label="Almacén de Origen"
            )
            self.fields['almacen_destino'] = forms.ModelChoiceField(
                queryset=Almacen.objects.filter(activo=True),
                widget=forms.Select(attrs={'class': 'form-control'}),
                label="Almacén de Destino"
            )
        elif tipo == 'ajuste':
            self.fields['almacen_origen'] = forms.ModelChoiceField(
                queryset=Almacen.objects.filter(activo=True),
                widget=forms.Select(attrs={'class': 'form-control'}),
                label="Almacén"
            )

class DetalleMovimientoForm(forms.ModelForm):
    class Meta:
        model = DetalleMovimientoAlmacen
        fields = ['material', 'cantidad', 'lote', 'costo_unitario']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'lote': forms.TextInput(attrs={'class': 'form-control'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


DetalleMovimientoFormSet = forms.inlineformset_factory(
    MovimientoAlmacen,
    DetalleMovimientoAlmacen,
    form=DetalleMovimientoForm,
    extra=1,
    can_delete=True
)

class EntradaMovimientoForm(forms.ModelForm):
    class Meta:
        model = MovimientoAlmacen
        fields = ['almacen_destino', 'documento_referencia', 'notas']
        widgets = {
            'almacen_destino': forms.Select(attrs={'class': 'form-control'}),
            'documento_referencia': forms.TextInput(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'almacen_destino': 'Almacén de Destino',
        }

class SalidaMovimientoForm(forms.ModelForm):
    class Meta:
        model = MovimientoAlmacen
        fields = ['almacen_origen', 'documento_referencia', 'notas']
        widgets = {
            'almacen_origen': forms.Select(attrs={'class': 'form-control'}),
            'documento_referencia': forms.TextInput(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'almacen_origen': 'Almacén de Origen',
        }

class TransferenciaMovimientoForm(forms.ModelForm):
    class Meta:
        model = MovimientoAlmacen
        fields = ['almacen_origen', 'almacen_destino', 'documento_referencia', 'notas']
        widgets = {
            'almacen_origen': forms.Select(attrs={'class': 'form-control'}),
            'almacen_destino': forms.Select(attrs={'class': 'form-control'}),
            'documento_referencia': forms.TextInput(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'almacen_origen': 'Almacén de Origen',
            'almacen_destino': 'Almacén de Destino',
        }
