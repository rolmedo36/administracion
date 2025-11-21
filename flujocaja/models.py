from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum

# --- BANCOS ---
class Banco(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    pais = models.CharField(max_length=50, default="México")
    swift = models.CharField(max_length=20, blank=True, help_text="Código SWIFT para transferencias internacionales")
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Banco"
        verbose_name_plural = "Bancos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

# --- CUENTAS BANCARIAS ---
TIPO_CUENTA_CHOICES = [
    ('corriente', 'Cuenta Corriente'),
    ('ahorro', 'Cuenta de Ahorro'),
    ('inversion', 'Cuenta de Inversión'),
]

MONEDA_CHOICES = [
    ('MXN', 'Pesos Mexicanos'),
    ('USD', 'Dólares Americanos'),
    ('EUR', 'Euros'),
]

class CuentaBancaria(models.Model):
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT, related_name='cuentas')
    numero_cuenta = models.CharField(max_length=50, unique=True)
    clabe = models.CharField(max_length=18, blank=True, help_text="CLABE interbancaria (México)")
    tipo_cuenta = models.CharField(max_length=20, choices=TIPO_CUENTA_CHOICES)
    moneda = models.CharField(max_length=10, choices=MONEDA_CHOICES, default='MXN')
    saldo_actual = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    descripcion = models.TextField(blank=True, help_text="Breve descripción de la cuenta")
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cuenta Bancaria"
        verbose_name_plural = "Cuentas Bancarias"
        ordering = ['banco__nombre', 'numero_cuenta']

    def __str__(self):
        return f"{self.banco.nombre} - {self.numero_cuenta}"


# Movimientos de caja
TIPO_FLUJO_CHOICES = [
    ('ingreso', 'Ingreso'),
    ('egreso', 'Egreso'),
]

TIPO_DOCUMENTO_CHOICES = [
    ('factura_venta', 'Factura de Venta'),
    ('factura_compra', 'Factura de Proveedor'),
    ('cobro_cliente', 'Cobro Cliente'),
    ('pago_proveedor', 'Pago Proveedor'),
    ('transferencia', 'Transferencia'),
    ('cheque', 'Cheque'),
    ('efectivo', 'Efectivo'),
    ('otro', 'Otro'),
]


class MovimientoBancario(models.Model):
    cuenta_bancaria = models.ForeignKey(CuentaBancaria, on_delete=models.PROTECT, related_name='movimientos')
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_FLUJO_CHOICES)
    monto = models.DecimalField(max_digits=18, decimal_places=2)
    fecha = models.DateField()
    descripcion = models.TextField()
    referencia = models.CharField(max_length=100, blank=True)  # Número de cheque, transferencia, etc.

    # Documento relacionado
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES)
    documento_id = models.PositiveIntegerField(null=True, blank=True)  # ID genérico
    documento_numero = models.CharField(max_length=50, blank=True)  # Folio, número OC, factura, etc.

    # Auditoría
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Estado
    estado = models.CharField(max_length=20, choices=[
        ('registrado', 'Registrado'),
        ('conciliado', 'Conciliado'),
        ('cancelado', 'Cancelado'),
    ], default='registrado')

    class Meta:
        verbose_name = "Movimiento Bancario"
        verbose_name_plural = "Movimientos Bancarios"
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - {self.monto} ({self.fecha})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Actualizar saldo de la cuenta bancaria
        ingresos = self.cuenta_bancaria.movimientos.filter(
            estado='registrado',
            tipo_movimiento='ingreso'
        ).aggregate(total=Sum('monto'))['total'] or 0

        egresos = self.cuenta_bancaria.movimientos.filter(
            estado='registrado',
            tipo_movimiento='egreso'
        ).aggregate(total=Sum('monto'))['total'] or 0

        self.cuenta_bancaria.saldo_actual = ingresos - egresos
        self.cuenta_bancaria.save(update_fields=['saldo_actual'])

