# materiales/forms.py
from django import forms
from .models import Material, CategoriaMaterial

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = [
            'codigo', 'nombre', 'descripcion', 'categoria',
            'unidad_medida', 'precio_unitario', 'es_inventariable',
            'stock_actual', 'stock_minimo', 'activo'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01'}),
            'stock_actual': forms.NumberInput(attrs={'step': '0.01'}),
            'stock_minimo': forms.NumberInput(attrs={'step': '0.01'}),
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