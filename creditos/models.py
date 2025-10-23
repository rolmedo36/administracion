# creditos/models.py
from django.db import models
from django.contrib.auth.models import User
from compras.models import Proveedor
from decimal import Decimal

METODO_AMORTIZACION_CHOICES = [
    ('frances', 'Método Francés (Cuota Fija)'),
    ('americano', 'Método Americano (Interés Periódico)'),
]

ESTADO_CREDITO_CHOICES = [
    ('activo', 'Activo'),
    ('pagado', 'Pagado'),
    ('cancelado', 'Cancelado'),
]

ESTADO_AMORTIZACION_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('pagado', 'Pagado'),
    ('vencido', 'Vencido'),
]

FRECUENCIA_PAGOS_CHOICES = [
    ('mensual', 'Mensual'),
    ('quincenal', 'Quincenal'),
    ('semanal', 'Semanal'),
]


class CreditoProveedor(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    monto_original = models.DecimalField(max_digits=14, decimal_places=2)
    saldo_actual = models.DecimalField(max_digits=14, decimal_places=2)
    tasa_interes = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Tasa mensual en porcentaje (ej: 2.5 para 2.5%)"
    )
    fecha_desembolso = models.DateField()
    fecha_inicio_pagos = models.DateField()
    frecuencia_pagos = models.CharField(max_length=20, choices=FRECUENCIA_PAGOS_CHOICES)
    num_cuotas = models.PositiveIntegerField()
    metodo_calculo = models.CharField(max_length=20, choices=METODO_AMORTIZACION_CHOICES)
    descripcion = models.TextField(blank=True, null=True)
    referencia = models.CharField(max_length=100, unique=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CREDITO_CHOICES, default='activo')
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Crédito con Proveedor"
        verbose_name_plural = "Créditos con Proveedores"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Crédito {self.referencia} - {self.proveedor.nombre}"

    def calcular_amortizaciones(self):
        from .utils import generar_amortizacion_frances, generar_amortizacion_americano

        if self.metodo_calculo == 'frances':
            return generar_amortizacion_frances(self)
        else:
            return generar_amortizacion_americano(self)


class AmortizacionCredito(models.Model):
    credito = models.ForeignKey(CreditoProveedor, on_delete=models.CASCADE, related_name='amortizaciones')
    numero_cuota = models.PositiveIntegerField()
    fecha_vencimiento = models.DateField()
    capital = models.DecimalField(max_digits=14, decimal_places=2)
    interes = models.DecimalField(max_digits=14, decimal_places=2)
    monto_total = models.DecimalField(max_digits=14, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_AMORTIZACION_CHOICES, default='pendiente')
    fecha_pago = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['numero_cuota']
        unique_together = ('credito', 'numero_cuota')

    def __str__(self):
        return f"Cuota {self.numero_cuota} - {self.credito.referencia}"


class PagoCredito(models.Model):
    amortizacion = models.ForeignKey(AmortizacionCredito, on_delete=models.CASCADE, related_name='pagos')
    monto_pagado = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_pago = models.DateField()
    referencia_pago = models.CharField(max_length=100, blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar estado de la amortización
        amort = self.amortizacion
        if self.monto_pagado >= amort.monto_total:
            amort.estado = 'pagado'
            amort.fecha_pago = self.fecha_pago
            amort.save()
            # Actualizar saldo del crédito
            credito = amort.credito
            credito.saldo_actual = max(Decimal('0'), credito.saldo_actual - amort.capital)
            if credito.saldo_actual <= 0:
                credito.estado = 'pagado'
            credito.save()