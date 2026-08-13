from django import forms
from .models import Mecanico, Vehiculo, OrdenServicio, ItemOrdenServicio, PagoOrdenServicio
from materiales.models import Almacen, Material

class MecanicoForm(forms.ModelForm):
    """Formulario para crear/editar mecánicos"""

    class Meta:
        model = Mecanico
        fields = ['nombre', 'apellido', 'telefono', 'email', 'especialidad', 'activo', 'notas', 'usuario']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@ejemplo.com'}),
            'especialidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Mecánica general'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'usuario': forms.Select(attrs={'class': 'form-select'}),
        }


class VehiculoForm(forms.ModelForm):
    """Formulario para crear/editar vehículos"""

    class Meta:
        model = Vehiculo
        fields = ['cliente', 'tipo', 'marca', 'modelo', 'año', 'placa', 'color',
                  'vin', 'cilindrada', 'kilometraje_actual', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Honda'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: CB190'}),
            'año': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2023'}),
            'placa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ABC-123'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rojo'}),
            'vin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '17 caracteres', 'maxlength': '17'}),
            'cilindrada': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'CC'}),
            'kilometraje_actual': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Kilómetros'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class OrdenServicioForm(forms.ModelForm):
    """Formulario para crear/editar órdenes de servicio"""

    class Meta:
        model = OrdenServicio
        fields = ['cliente', 'vehiculo', 'mecanico_responsable', 'tipo_servicio',
                  'kilometraje_entrada', 'sintoma_cliente', 'diagnostico_mecanico',
                  'costo_diagnostico', 'diagnostico_aplicado', 'notas_tecnicas',
                  'descuento', 'metodo_pago', 'garantia_dias']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'vehiculo': forms.Select(attrs={'class': 'form-select'}),
            'mecanico_responsable': forms.Select(attrs={'class': 'form-select'}),
            'tipo_servicio': forms.Select(attrs={'class': 'form-select'}),
            'kilometraje_entrada': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Kilómetros'}),
            'sintoma_cliente': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                     'placeholder': 'Lo que el cliente reporta'}),
            'diagnostico_mecanico': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                          'placeholder': 'Lo que el mecánico encontró'}),
            'costo_diagnostico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'diagnostico_aplicado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notas_tecnicas': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                                    'placeholder': 'Detalle del trabajo realizado'}),
            'descuento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
            'garantia_dias': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si es una orden existente y ya tiene cliente asignado
        if self.instance.pk and self.instance.cliente_id:
            self.fields['vehiculo'].queryset = Vehiculo.objects.filter(cliente=self.instance.cliente)
        else:
            # Si es una orden nueva, revisamos si el usuario seleccionó un cliente en el formulario
            cliente_id = self.data.get('cliente') if self.data else None

            if cliente_id:
                # Si hay un cliente en los datos enviados (POST), filtrar sus vehículos
                self.fields['vehiculo'].queryset = Vehiculo.objects.filter(cliente_id=cliente_id)
            else:
                # Si no hay cliente seleccionado aún (carga inicial), mostrar todos los vehículos
                self.fields['vehiculo'].queryset = Vehiculo.objects.all()


class ItemOrdenServicioForm(forms.ModelForm):
    """Formulario para crear/editar ítems de orden de servicio"""

    class Meta:
        model = ItemOrdenServicio
        fields = ['tipo', 'material', 'almacen', 'descripcion', 'cantidad', 'precio_unitario']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'material': forms.Select(attrs={'class': 'form-select', 'id': 'id_material_select'}),
            'almacen': forms.Select(attrs={'class': 'form-select', 'id': 'id_almacen_select'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción del ítem'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Por defecto, mostrar solo almacenes activos
        self.fields['almacen'].queryset = Almacen.objects.filter(activo=True)


class PagoOrdenServicioForm(forms.ModelForm):
    """Formulario para registrar pagos de una orden"""

    class Meta:
        model = PagoOrdenServicio
        fields = ['monto', 'metodo_pago', 'referencia', 'notas']
        widgets = {
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
            'referencia': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'No. Factura, Transferencia, etc.'}),
            'notas': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observaciones del pago'}),
        }