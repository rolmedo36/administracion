from django.db.models import Sum
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from materiales.models import Material
from decimal import Decimal

class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    identificacion = models.CharField("RFC", max_length=50, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.identificacion})"

ESTADO_OC_CHOICES = [
    ('borrador', 'Borrador'),
    ('confirmada', 'Confirmada'),
    ('recibida', 'Recibida'),
    ('cancelada', 'Cancelada'),
]

class OrdenCompra(models.Model):
    numero = models.CharField(max_length=50, unique=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    fecha_emision = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_OC_CHOICES, default='borrador')
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def get_estado_badge_class(self):
        if self.estado == 'borrador':
            return 'secondary'
        elif self.estado == 'confirmada':
            return 'primary'
        elif self.estado == 'recibida':
            return 'success'
        elif self.estado == 'cancelada':
            return 'danger'
        return 'light'

    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"
        ordering = ['-fecha_creacion']

    def puede_recibirse(self):
        return self.estado == 'confirmada'

    def recibir(self, usuario, referencia, fecha_vencimiento, almacen):
        if not self.puede_recibirse():
            raise ValueError("La orden debe estar en estado 'Confirmada' para ser recibida.")

        # Actualizar stock por almacén
        from materiales.models import StockAlmacen
        for detalle in self.detalles.all():
            if detalle.material.es_inventariable:
                stock, created = StockAlmacen.objects.get_or_create(
                    material=detalle.material,
                    almacen=almacen,
                    defaults={'cantidad': 0}
                )
                stock.cantidad += detalle.cantidad
                stock.save(update_fields=['cantidad'])

        self.estado = 'recibida'
        self.save(update_fields=['estado'])

        # Crear CXP
        from .models import CuentaPorPagar
        CuentaPorPagar.objects.create(
            orden_compra=self,
            proveedor=self.proveedor,
            monto_total=self.total,
            saldo_pendiente=self.total,
            referencia=referencia,
            fecha_vencimiento=fecha_vencimiento,
            creado_por=usuario
        )

    def clean(self):
        if self.pk:  # Solo en edición
            original = OrdenCompra.objects.get(pk=self.pk)
            if original.estado in ['recibida', 'cancelada']:
                if self.estado != original.estado:
                    raise ValidationError("No se puede modificar el estado de una orden recibida o cancelada.")

    def __str__(self):
        return f"OC-{self.numero} - {self.proveedor.nombre}"

class DetalleOrdenCompra(models.Model):
    orden = models.ForeignKey(OrdenCompra, related_name='detalles', on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    aplica_iva = models.BooleanField(default=False)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)  # Precio base (sin IVA)
    precio_con_iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Precio con IVA
    aplica_iva = models.BooleanField(default=False)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.pk and self.material:
            self.aplica_iva = self.material.aplica_iva

        # Calcular precio con IVA
        if self.aplica_iva:
            self.precio_con_iva = self.precio_unitario * Decimal('1.16')
        else:
            self.precio_con_iva = self.precio_unitario

        # Calcular subtotal con precio_con_iva
        self.subtotal = self.cantidad * self.precio_con_iva
        super().save(*args, **kwargs)

# CXP
ESTADO_CXP_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('parcial', 'Pago Parcial'),
    ('pagado', 'Pagado'),
]

class CuentaPorPagar(models.Model):
    orden_compra = models.OneToOneField(OrdenCompra, on_delete=models.CASCADE, related_name='cuenta_por_pagar')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    monto_total = models.DecimalField(max_digits=14, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=14, decimal_places=2)
    referencia = models.CharField("Factura/Referencia", max_length=100)
    fecha_emision = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CXP_CHOICES, default='pendiente')
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cuenta por Pagar"
        verbose_name_plural = "Cuentas por Pagar"
        ordering = ['-fecha_emision']

    def __str__(self):
        return f"CXP-{self.id} - {self.proveedor.nombre} - {self.referencia}"

    def esta_pagado(self):
        return self.saldo_pendiente <= 0

    def save(self, *args, **kwargs):
        if self.saldo_pendiente <= 0:
            self.estado = 'pagado'
        elif self.saldo_pendiente < self.monto_total:
            self.estado = 'parcial'
        else:
            self.estado = 'pendiente'
        super().save(*args, **kwargs)

    def get_saldo_class(self):
        return 'success' if self.saldo_pendiente <= 0 else 'danger'

class PagoCuentaPorPagar(models.Model):
    cuenta_por_pagar = models.ForeignKey(CuentaPorPagar, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_pago = models.DateField()
    referencia = models.CharField("Referencia (comprobante)", max_length=100, blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pago de Cuenta por Pagar"
        verbose_name_plural = "Pagos de Cuentas por Pagar"
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago de ${self.monto} - {self.cuenta_por_pagar.referencia}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar saldo de la CXP
        cxp = self.cuenta_por_pagar
        total_pagado = cxp.pagos.aggregate(total=models.Sum('monto'))['total'] or 0
        cxp.saldo_pendiente = cxp.monto_total - total_pagado
        if cxp.saldo_pendiente < 0:
            cxp.saldo_pendiente = 0
        cxp.save(update_fields=['saldo_pendiente'])
