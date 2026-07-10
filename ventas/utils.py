from django.db import transaction
from django.utils import timezone
from .models import FacturaVenta, DetalleFactura, CuentaPorCobrar, PedidoVenta
from materiales.models import StockAlmacen
from decimal import Decimal


def surtir_pedido(pedido, usuario, almacen_id=None):
    """
    Surtir un pedido y generar factura.
    Si no se especifica almacén, se usará el primero disponible con stock.
    """
    with transaction.atomic():
        # Verificar stock disponible
        for detalle_pedido in pedido.detalles.all():
            if detalle_pedido.material.es_inventariable:
                # Obtener stock total del material en todos los almacenes
                stocks = StockAlmacen.objects.filter(
                    material=detalle_pedido.material
                )

                if not stocks.exists():
                    raise ValueError(f"No hay stock disponible para {detalle_pedido.material.nombre}")

                # Calcular stock total disponible
                stock_total = sum(stock.cantidad for stock in stocks)

                if stock_total < detalle_pedido.cantidad_solicitada:
                    raise ValueError(
                        f"Stock insuficiente para {detalle_pedido.material.nombre}. "
                        f"Solicitado: {detalle_pedido.cantidad_solicitada}, "
                        f"Disponible: {stock_total}"
                    )

                # Si no se especifica almacén, usar el primero con stock suficiente
                if not almacen_id:
                    for stock in stocks:
                        if stock.cantidad >= detalle_pedido.cantidad_solicitada:
                            almacen_id = stock.almacen.id
                            break
                    # Si no hay un almacén con suficiente stock individual,
                    # se usará el almacén con más stock
                    if not almacen_id:
                        # Tomar el almacén con más stock
                        almacen_id = max(stocks, key=lambda s: s.cantidad).almacen.id

        # Actualizar stock y marcar como surtido
        subtotal_total = Decimal('0')
        iva_total = Decimal('0')

        for detalle_pedido in pedido.detalles.all():
            if detalle_pedido.material.es_inventariable:
                cantidad_a_surtir = detalle_pedido.cantidad_solicitada

                # Manejar surtido desde múltiples almacenes si es necesario
                while cantidad_a_surtir > 0:
                    # Buscar stock disponible en el almacén especificado
                    stock_almacen = StockAlmacen.objects.get(
                        material=detalle_pedido.material,
                        almacen_id=almacen_id
                    )

                    if stock_almacen.cantidad >= cantidad_a_surtir:
                        # Stock suficiente en este almacén
                        stock_almacen.cantidad -= cantidad_a_surtir
                        stock_almacen.save()
                        cantidad_a_surtir = 0
                    else:
                        cantidad_a_surtir -= stock_almacen.cantidad
                        stock_almacen.cantidad = 0
                        stock_almacen.save()
                        # Buscar otro almacén con stock
                        otro_stock = StockAlmacen.objects.filter(
                            material=detalle_pedido.material,
                            cantidad__gt=0
                        ).exclude(almacen_id=almacen_id).first()

                        if otro_stock:
                            almacen_id = otro_stock.almacen.id
                        else:
                            raise ValueError(
                                f"Stock insuficiente para completar el surtido de {detalle_pedido.material.nombre}"
                            )

                # Actualizar cantidad surtida
                detalle_pedido.cantidad_surtida = detalle_pedido.cantidad_solicitada
                detalle_pedido.save()

                # ✅ ASEGURAR QUE subtotal_detalle SEA Decimal
                subtotal_detalle = detalle_pedido.subtotal
                if not isinstance(subtotal_detalle, Decimal):
                    subtotal_detalle = Decimal(str(subtotal_detalle))

                subtotal_total += subtotal_detalle

                # ✅ USAR Decimal PARA EL IVA
                if detalle_pedido.material.aplica_iva:
                    iva_detalle = subtotal_detalle * Decimal('0.16')  # ✅ Decimal * Decimal
                    iva_total += iva_detalle

        # Actualizar estado del pedido
        pedido.estado = 'completo'
        pedido.save()

        # Generar factura
        factura = FacturaVenta.objects.create(
            cliente=pedido.cliente,
            pedido=pedido,
            folio=f"FAC-{pedido.id:06d}",
            subtotal=subtotal_total,
            iva=iva_total,
            total=subtotal_total + iva_total,
            creado_por=usuario,
            fecha=timezone.now().date(),
            vendedor=pedido.vendedor,

        )

        # Crear detalles de factura
        for detalle_pedido in pedido.detalles.all():
            # ✅ ASEGURAR QUE LOS VALORES SEAN Decimal
            cantidad = Decimal(str(detalle_pedido.cantidad_solicitada))
            precio_unitario = Decimal(str(detalle_pedido.precio_unitario))
            descuento = Decimal(str(detalle_pedido.descuento))

            DetalleFactura.objects.create(
                factura=factura,
                material=detalle_pedido.material,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                descuento=descuento,
                iva_porcentaje=Decimal('16.00') if detalle_pedido.material.aplica_iva else Decimal('0'),
                # iva_monto y subtotal se calcularán en el save() del modelo
            )

        # Generar Cuenta por Cobrar
        CuentaPorCobrar.objects.create(
            factura=factura,
            cliente=pedido.cliente,
            monto_total=factura.total,
            saldo_pendiente=factura.total,
            fecha_vencimiento=timezone.now().date()
        )

        return factura