from .models import PedidoVenta, FacturaVenta, CuentaPorCobrar
from materiales.models import StockAlmacen


def surtir_pedido(pedido, almacen_id, usuario):
    """Surtir un pedido y generar factura."""
    from django.utils import timezone

    # Verificar stock disponible
    for detalle in pedido.detalles.all():
        if detalle.material.es_inventariable:
            stock = StockAlmacen.objects.filter(
                material=detalle.material,
                almacen_id=almacen_id
            ).first()
            if not stock or stock.cantidad < detalle.cantidad_solicitada:
                raise ValueError(f"Stock insuficiente para {detalle.material.nombre}")

    # Actualizar stock
    for detalle in pedido.detalles.all():
        if detalle.material.es_inventariable:
            stock = StockAlmacen.objects.get(
                material=detalle.material,
                almacen_id=almacen_id
            )
            stock.cantidad -= detalle.cantidad_solicitada
            stock.save()
            detalle.cantidad_surtida = detalle.cantidad_solicitada
            detalle.save()

    # Actualizar estado del pedido
    pedido.estado = 'completo'
    pedido.save()

    # Generar factura
    factura = FacturaVenta.objects.create(
        cliente=pedido.cliente,
        pedido=pedido,
        folio=f"FAC-{pedido.id:06d}",
        creado_por=usuario
    )

    # Crear detalles de factura
    subtotal_total = 0
    iva_total = 0
    for detalle in pedido.detalles.all():
        detalle_factura = DetalleFactura.objects.create(
            factura=factura,
            material=detalle.material,
            cantidad=detalle.cantidad_solicitada,
            precio_unitario=detalle.precio_unitario,
            descuento=detalle.descuento,
            iva_porcentaje=16.00 if detalle.material.aplica_iva else 0
        )
        subtotal_total += detalle_factura.subtotal
        iva_total += detalle_factura.iva_monto

    factura.subtotal = subtotal_total
    factura.iva = iva_total
    factura.total = subtotal_total + iva_total
    factura.save()

    # Generar Cuenta por Cobrar
    CuentaPorCobrar.objects.create(
        factura=factura,
        cliente=pedido.cliente,
        monto_total=factura.total,
        saldo_pendiente=factura.total,
        fecha_vencimiento=timezone.now().date()  # Ajustar según política
    )

    return factura