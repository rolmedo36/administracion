from django.db.models import Sum
from django.db import models
from django.contrib.auth.models import User
from clientes.models import Cliente
from materiales.models import Material, Almacen
from flujocaja.models import CuentaBancaria

# Choices
ESTADO_COTIZACION_CHOICES = [
    ('borrador', 'Borrador'),
    ('enviada', 'Enviada'),
    ('aceptada', 'Aceptada'),
    ('rechazada', 'Rechazada'),
    ('convertida', 'Convertida a Pedido'),
]

ESTADO_PEDIDO_CHOICES = [
    ('borrador', 'Borrador'),
    ('confirmado', 'Confirmado'),
    ('parcial', 'Surtido Parcial'),
    ('completo', 'Surtido Completo'),
    ('cancelado', 'Cancelado'),
]

ESTADO_FACTURA_CHOICES = [
    ('activa', 'Activa'),
    ('cancelada', 'Cancelada'),
]

ESTADO_CXC_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('parcial', 'Pago Parcial'),
    ('pagado', 'Pagado'),
]


class CotizacionVenta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    fecha = models.DateField(auto_now_add=True)
    dias_validez = models.PositiveIntegerField(default=30)
    estado = models.CharField(max_length=20, choices=ESTADO_COTIZACION_CHOICES, default='borrador')
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    notas = models.TextField(blank=True, null=True, help_text="Observaciones")

    class Meta:
        verbose_name = "Cotización de Venta"
        verbose_name_plural = "Cotizaciones de Venta"

    def __str__(self):
        return f"COT-{self.id} - {self.cliente.nombre}"


class DetalleCotizacion(models.Model):
    cotizacion = models.ForeignKey(CotizacionVenta, related_name='detalles', on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # %
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        descuento_decimal = self.descuento / 100
        precio_con_descuento = self.precio_unitario * (1 - descuento_decimal)
        self.subtotal = self.cantidad * precio_con_descuento
        super().save(*args, **kwargs)


class PedidoVenta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    cotizacion = models.ForeignKey(CotizacionVenta, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_PEDIDO_CHOICES, default='borrador')
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    notas = models.TextField(blank=True, null=True, help_text="Observaciones")

    class Meta:
        verbose_name = "Pedido de Venta"
        verbose_name_plural = "Pedidos de Venta"

    def __str__(self):
        return f"PED-{self.id} - {self.cliente.nombre}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(PedidoVenta, related_name='detalles', on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    cantidad_solicitada = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_surtida = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    @property
    def pendiente_surtir(self):
        return self.cantidad_solicitada - self.cantidad_surtida


class FacturaVenta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    pedido = models.ForeignKey(PedidoVenta, on_delete=models.SET_NULL, null=True, blank=True)
    folio = models.CharField(max_length=50, unique=True)
    fecha = models.DateField()
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_FACTURA_CHOICES, default='activa')
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    # Campos para timbrado
    uuid = models.CharField(max_length=50, blank=True, null=True)
    folio_fiscal = models.CharField(max_length=50, blank=True, null=True)
    cadena_original = models.TextField(blank=True, null=True)
    fecha_timbrado = models.DateTimeField(blank=True, null=True)
    xml_timbrado = models.TextField(blank=True, null=True)
    pdf_timbrado = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=[
        ('borrador', 'Borrador'),
        ('activa', 'Activa'),
        ('timbrada', 'Timbrada'),
        ('cancelada', 'Cancelada'),
    ], default='activa')
    notas = models.TextField(blank=True, null=True, help_text="Observaciones")


    class Meta:
        verbose_name = "Factura de Venta"
        verbose_name_plural = "Facturas de Venta"

    def __str__(self):
        return f"FAC-{self.folio}"


class DetalleFactura(models.Model):
    factura = models.ForeignKey(FacturaVenta, related_name='detalles', on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    iva_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=16.00)
    iva_monto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Calcular subtotal con descuento
        descuento_decimal = self.descuento / 100
        precio_con_descuento = self.precio_unitario * (1 - descuento_decimal)
        self.subtotal = self.cantidad * precio_con_descuento

        # Calcular IVA
        iva_decimal = self.iva_porcentaje / 100
        self.iva_monto = self.subtotal * iva_decimal

        super().save(*args, **kwargs)


class CuentaPorCobrar(models.Model):
    factura = models.OneToOneField(FacturaVenta, on_delete=models.CASCADE, related_name='cuenta_por_cobrar')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    monto_total = models.DecimalField(max_digits=14, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CXC_CHOICES, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cuenta por Cobrar"
        verbose_name_plural = "Cuentas por Cobrar"

    def save(self, *args, **kwargs):
        if self.saldo_pendiente <= 0:
            self.estado = 'pagado'
        elif self.saldo_pendiente < self.monto_total:
            self.estado = 'parcial'
        else:
            self.estado = 'pendiente'
        super().save(*args, **kwargs)

class PagoCuentaPorCobrar(models.Model):
    cuenta_por_cobrar = models.ForeignKey('CuentaPorCobrar', on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_pago = models.DateField()
    referencia = models.CharField(max_length=100, blank=True)

    cuenta_bancaria = models.ForeignKey(
        'flujocaja.CuentaBancaria',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Cuenta Bancaria"
    )

    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pago de Cuenta por Cobrar"
        verbose_name_plural = "Pagos de Cuentas por Cobrar"
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago de ${self.monto} - {self.cuenta_por_cobrar.factura.folio}"
