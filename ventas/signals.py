from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from .models import PagoCuentaPorCobrar


@receiver(post_save, sender=PagoCuentaPorCobrar)
def actualizar_saldo_cxc(sender, instance, created, **kwargs):
    """
    Actualiza el saldo pendiente de la CxC cada vez que se registra un pago.
    """
    if created and instance.cuenta_por_cobrar_id:
        # Recalcular saldo
        cxc = instance.cuenta_por_cobrar
        total_pagado = cxc.pagos.aggregate(total=Sum('monto'))['total'] or 0
        cxc.saldo_pendiente = max(0, cxc.monto_total - total_pagado)

        # Actualizar estado
        if cxc.saldo_pendiente <= 0:
            cxc.estado = 'pagado'
        elif cxc.saldo_pendiente < cxc.monto_total:
            cxc.estado = 'parcial'
        else:
            cxc.estado = 'pendiente'

        cxc.save(update_fields=['saldo_pendiente', 'estado'])