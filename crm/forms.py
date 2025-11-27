from django import forms
from django.contrib.auth.models import User
from .models import Prospecto, Oportunidad, Cliente, Actividad, PlantillaEmail

class ProspectoForm(forms.ModelForm):
    class Meta:
        model = Prospecto
        fields = [
            'nombre', 'empresa', 'email', 'telefono', 'cargo',
            'origen', 'estado', 'fecha_proximo_contacto', 'notas', 'asignado_a'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'origen': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'fecha_proximo_contacto': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'asignado_a': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo usuarios activos y con permisos de ventas
        self.fields['asignado_a'].queryset = User.objects.filter(is_active=True)
        # Fecha próximo contacto opcional
        self.fields['fecha_proximo_contacto'].required = False

# OPORTUNIDADES

class OportunidadForm(forms.ModelForm):
    class Meta:
        model = Oportunidad
        fields = [
            'prospecto', 'cliente', 'nombre', 'descripcion',
            'monto_estimado', 'etapa', 'probabilidad',
            'fecha_cierre_estimada', 'fecha_proximo_contacto', 'asignado_a'
        ]
        widgets = {
            'prospecto': forms.Select(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'monto_estimado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'etapa': forms.Select(attrs={'class': 'form-control'}),
            'probabilidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'fecha_cierre_estimada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_proximo_contacto': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'asignado_a': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar prospectos calificados y activos
        self.fields['prospecto'].queryset = Prospecto.objects.filter(
            estado='calificado',
            activo=True
        )
        # Solo clientes activos
        self.fields['cliente'].queryset = Cliente.objects.filter(activo=True)
        # Solo usuarios activos
        self.fields['asignado_a'].queryset = User.objects.filter(is_active=True)

        # Campos opcionales
        self.fields['fecha_cierre_estimada'].required = False
        self.fields['fecha_proximo_contacto'].required = False
        self.fields['cliente'].required = False

        # Auto-asignar probabilidad según etapa
        if not self.initial.get('probabilidad') and self.initial.get('etapa'):
            self.fields['probabilidad'].initial = self._get_probabilidad_por_etapa(self.initial['etapa'])

    def _get_probabilidad_por_etapa(self, etapa):
        """Retorna la probabilidad por defecto según la etapa."""
        probabilidad_por_etapa = {
            'prospecto': 0,
            'contacto': 10,
            'necesidades': 25,
            'propuesta': 50,
            'negociacion': 75,
            'ganado': 100,
            'perdido': 0,
        }
        return probabilidad_por_etapa.get(etapa, 0)

    def clean(self):
        cleaned_data = super().clean()
        prospecto = cleaned_data.get('prospecto')
        cliente = cleaned_data.get('cliente')

        # Validar que tenga al menos prospecto o cliente
        if not prospecto and not cliente:
            raise forms.ValidationError("Debe seleccionar un prospecto o un cliente.")

        # Si tiene prospecto, no puede tener cliente (o viceversa)
        # if prospecto and cliente:
        #     raise forms.ValidationError("No se puede tener prospecto y cliente al mismo tiempo.")

        return cleaned_data

# ACTIVIDADES

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = [
            'tipo', 'asunto', 'descripcion', 'fecha_hora',
            'prospecto', 'oportunidad', 'relacionado_con'
        ]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'asunto': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_hora': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'prospecto': forms.Select(attrs={'class': 'form-control'}),
            'oportunidad': forms.Select(attrs={'class': 'form-control'}),
            'relacionado_con': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar prospectos y oportunidades activos
        self.fields['prospecto'].queryset = Prospecto.objects.filter(activo=True)
        self.fields['oportunidad'].queryset = Oportunidad.objects.filter(activo=True)
        self.fields['relacionado_con'].queryset = User.objects.filter(is_active=True)

        # Campos opcionales
        self.fields['prospecto'].required = False
        self.fields['oportunidad'].required = False

        # Validación: debe tener al menos prospecto u oportunidad
        if not self.initial.get('prospecto') and not self.initial.get('oportunidad'):
            self.fields['prospecto'].widget.attrs['class'] += ' is-invalid'

    def clean(self):
        cleaned_data = super().clean()
        prospecto = cleaned_data.get('prospecto')
        oportunidad = cleaned_data.get('oportunidad')

        if not prospecto and not oportunidad:
            raise forms.ValidationError("La actividad debe estar relacionada con un prospecto o una oportunidad.")

        return cleaned_data

# PLANTILLA

class PlantillaEmailForm(forms.ModelForm):
    class Meta:
        model = PlantillaEmail
        fields = ['nombre', 'asunto', 'cuerpo', 'categoria', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'asunto': forms.TextInput(attrs={'class': 'form-control'}),
            'cuerpo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Puedes usar {{ nombre }} para personalizar el mensaje'
            }),
            'categoria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Bienvenida, Seguimiento, Oferta'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar ayuda sobre variables disponibles
        self.fields['cuerpo'].help_text = """
        <small class="text-muted">
            Variables disponibles: {{ nombre }}, {{ empresa }}, {{ fecha }}
        </small>
        """