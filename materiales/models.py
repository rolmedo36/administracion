# materiales/models.py
from django.db import models
from django.contrib.auth.models import User

UNIDAD_MEDIDA_CHOICES = [
    ('unidad', 'Unidad'),
    ('kg', 'Kilogramo (kg)'),
    ('g', 'Gramo (g)'),
    ('lt', 'Litro (lt)'),
    ('ml', 'Mililitro (ml)'),
    ('m', 'Metro (m)'),
    ('cm', 'Centímetro (cm)'),
    ('m2', 'Metro cuadrado (m²)'),
    ('m3', 'Metro cúbico (m³)'),
    ('h', 'Hora (h)'),
    ('día', 'Día'),
    ('caja', 'Caja'),
    ('rollo', 'Rollo'),
    ('paquete', 'Paquete'),
    ('servicio', 'Servicio'),
]

class CategoriaMaterial(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Categoría de Material"
        verbose_name_plural = "Categorías de Materiales"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Material(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(CategoriaMaterial, on_delete=models.PROTECT)
    unidad_medida = models.CharField(max_length=20, choices=UNIDAD_MEDIDA_CHOICES)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Precio unitario")
    es_inventariable = models.BooleanField(default=True, verbose_name="¿Es inventariable?")
    stock_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Stock actual")
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Stock mínimo")
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    aplica_iva = models.BooleanField(default=False, verbose_name="¿Aplica IVA?")

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    @property
    def tipo_display(self):
        return "📦 Inventariable" if self.es_inventariable else "⚙️ Servicio"

    @property
    def stock_bajo(self):
        return self.es_inventariable and self.stock_actual < self.stock_minimo

# ALMACENES

class Almacen(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Almacén"
        verbose_name_plural = "Almacenes"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class StockAlmacen(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='stocks')
    almacen = models.ForeignKey(Almacen, on_delete=models.CASCADE, related_name='stocks')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ('material', 'almacen')
        verbose_name = "Stock por Almacén"
        verbose_name_plural = "Stocks por Almacén"

    def __str__(self):
        return f"{self.material} en {self.almacen}: {self.cantidad}"