from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils import timezone

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
    cantidad_reservada = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cantidad_danada = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('material', 'almacen')
        verbose_name = "Stock por Almacén"
        verbose_name_plural = "Stocks por Almacén"

    def __str__(self):
        return f"{self.material} en {self.almacen}: {self.cantidad}"

TIPO_MOVIMIENTO_CHOICES = [
    ('entrada_compra', 'Entrada por Compra'),
    ('entrada_devolucion_venta', 'Devolución de Venta'),
    ('entrada_ajuste_positivo', 'Ajuste Positivo'),
    ('salida_venta', 'Salida por Venta'),
    ('salida_devolucion_compra', 'Devolución a Proveedor'),
    ('salida_ajuste_negativo', 'Ajuste Negativo'),
    ('transferencia', 'Transferencia entre Almacenes'),
    ('conteo_fisico', 'Conteo Físico'),
]

ESTADO_MOVIMIENTO_CHOICES = [
    ('borrador', 'Borrador'),
    ('confirmado', 'Confirmado'),
    ('cancelado', 'Cancelado'),
]


class MovimientoAlmacen(models.Model):
    tipo = models.CharField(max_length=50, choices=TIPO_MOVIMIENTO_CHOICES)
    fecha = models.DateTimeField(default=timezone.now)
    almacen_origen = models.ForeignKey('Almacen', on_delete=models.PROTECT, null=True, blank=True,
                                       related_name='movimientos_salida')
    almacen_destino = models.ForeignKey('Almacen', on_delete=models.PROTECT, null=True, blank=True,
                                        related_name='movimientos_entrada')
    documento_referencia = models.CharField(max_length=100, blank=True)  # OC-001, PED-001, etc.
    notas = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_MOVIMIENTO_CHOICES, default='borrador')
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    confirmado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='movimientos_confirmados')
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Movimiento de Almacén"
        verbose_name_plural = "Movimientos de Almacén"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha.strftime('%d/%m/%Y')}"

    def confirmar(self, usuario):
        from django.db import transaction
        with transaction.atomic():
            # Determinar el almacén correcto para ajustes
            almacen_para_ajuste = None

            if self.tipo in ['entrada_ajuste_positivo', 'salida_ajuste_negativo']:
                # Para ajustes, usar almacen_origen
                almacen_para_ajuste = self.almacen_origen
                if not almacen_para_ajuste:
                    raise ValueError("Almacén es requerido para ajustes")
            else:
                # Para otros movimientos, usar los almacenes normales
                almacen_para_ajuste = self.almacen_destino or self.almacen_origen

            # Validar stock para salidas y ajustes negativos
            if self.tipo.startswith('salida'):
                for detalle in self.detalles.all():
                    if self.tipo in ['salida_ajuste_negativo'] and not self.almacen_origen:
                        raise ValueError("Almacén es requerido para ajustes negativos")

                    # Usar el almacén correcto según el tipo
                    almacen_validar = self.almacen_origen if self.tipo in [
                        'salida_ajuste_negativo'] else self.almacen_origen

                    if almacen_validar:
                        stock = StockAlmacen.objects.get(
                            material=detalle.material,
                            almacen=almacen_validar
                        )
                        if stock.cantidad < detalle.cantidad:
                            raise ValueError(f"Stock insuficiente para {detalle.material.nombre}")
                    else:
                        raise ValueError("Almacén de origen es requerido para salidas")

            # Actualizar stocks
            for detalle in self.detalles.all():
                if self.tipo.startswith('entrada'):
                    # Entradas y ajustes positivos
                    almacen_usar = self.almacen_destino
                    if self.tipo == 'entrada_ajuste_positivo':
                        almacen_usar = self.almacen_origen

                    if not almacen_usar:
                        raise ValueError("Almacén es requerido")

                    stock, created = StockAlmacen.objects.get_or_create(
                        material=detalle.material,
                        almacen=almacen_usar,
                        defaults={'cantidad': 0}
                    )
                    stock.cantidad += detalle.cantidad
                    stock.save()

                elif self.tipo.startswith('salida'):
                    # Salidas y ajustes negativos
                    almacen_usar = self.almacen_origen
                    if not almacen_usar:
                        raise ValueError("Almacén es requerido")

                    stock = StockAlmacen.objects.get(
                        material=detalle.material,
                        almacen=almacen_usar
                    )
                    stock.cantidad -= detalle.cantidad
                    stock.save()

            self.estado = 'confirmado'
            self.confirmado_por = usuario
            self.fecha_confirmacion = timezone.now()
            self.save()

class DetalleMovimientoAlmacen(models.Model):
    movimiento = models.ForeignKey(MovimientoAlmacen, related_name='detalles', on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    lote = models.CharField(max_length=100, blank=True)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    referencia = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.material.nombre} - {self.cantidad}"

