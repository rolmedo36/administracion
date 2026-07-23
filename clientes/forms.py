from django import forms
from .models import Cliente, ActividadCliente, DocumentoCliente


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

class ActividadClienteForm(forms.ModelForm):
    # Personalizamos el campo de fecha para que sea más amigable
    fecha_programada = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            },
            format='%Y-%m-%dT%H:%M'
        ),
        help_text="Opcional para comentarios. Requerido para tareas y eventos."
    )

    class Meta:
        model = ActividadCliente
        fields = ['tipo', 'titulo', 'descripcion', 'fecha_programada', 'estado', 'es_privado']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Llamar para seguimiento de cotización'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalles de la actividad...'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'es_privado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DocumentoClienteForm(forms.ModelForm):
    class Meta:
        model = DocumentoCliente
        fields = ['tipo', 'archivo', 'descripcion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'archivo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Contrato firmado versión 2024'
            }),
        }

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Validar tamaño (máximo 10MB)
            if archivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError("El archivo no debe superar los 10MB.")

            # Validar extensión
            extension = archivo.name.split('.')[-1].lower()
            if extension not in ['pdf', 'jpg', 'jpeg', 'png']:
                raise forms.ValidationError("Solo se permiten archivos PDF, JPG o PNG.")

        return archivo
