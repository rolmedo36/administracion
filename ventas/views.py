from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction
from .models import CotizacionVenta, PedidoVenta, DetallePedido, Cliente, Material, DetalleCotizacion, FacturaVenta, DetalleFactura, CuentaPorCobrar, PagoCuentaPorCobrar
from .forms import (
    CotizacionVentaForm,
    DetalleCotizacionFormSet,
    PedidoVentaForm,
    DetallePedidoForm,
    DetallePedidoFormSet,
    FacturaVentaForm,
    DetalleFacturaForm,
    DetalleFacturaFormSet,
    PagoCuentaPorCobrarForm
)
from django.http import JsonResponse
from datetime import date, timedelta
from django.db.models import Case, When, IntegerField, Sum
from django.db import models
from flujocaja.models import MovimientoBancario

@login_required
@permission_required('ventas.view_cotizacionventa', raise_exception=True)
def cotizacion_list(request):
    cotizaciones = CotizacionVenta.objects.select_related('cliente').all().order_by('-fecha')
    return render(request, 'ventas/cotizacion/cotizacion_list.html', {
        'cotizaciones': cotizaciones
    })


@login_required
@permission_required('ventas.add_cotizacionventa', raise_exception=True)
def cotizacion_create(request):
    if request.method == 'POST':
        form = CotizacionVentaForm(request.POST)
        formset = DetalleCotizacionFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    cotizacion = form.save(commit=False)
                    cotizacion.creado_por = request.user
                    cotizacion.save()

                    detalles = formset.save(commit=False)
                    for detalle in detalles:
                        # Asegurar descuento = 0 si es None
                        if detalle.descuento is None:
                            detalle.descuento = 0
                        detalle.cotizacion = cotizacion
                        detalle.save()
                    for detalle in formset.deleted_objects:
                        detalle.delete()

                    total = sum(detalle.subtotal for detalle in cotizacion.detalles.all())
                    cotizacion.total = total
                    cotizacion.save()

                    messages.success(request, f"Cotización {cotizacion.id} creada exitosamente.")
                    return redirect('ventas:cotizacion_detail', pk=cotizacion.pk)
            except Exception as e:
                messages.error(request, f"Error al crear la cotización: {str(e)}")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = CotizacionVentaForm()
        # Crear formset con exactamente 1 formulario vacío
        formset = DetalleCotizacionFormSet(
            queryset=DetalleCotizacion.objects.none(),
            initial=[{'descuento': 0}]  # ← Forzar descuento = 0
        )

    clientes = Cliente.objects.filter(activo=True)
    materiales = Material.objects.filter(activo=True, es_inventariable=True)

    return render(request, 'ventas/cotizacion/cotizacion_form.html', {
        'form': form,
        'formset': formset,
        'empty_form': formset.empty_form,
        'clientes': clientes,
        'materiales': materiales,
        'object': None,
    })

@login_required
@permission_required('ventas.view_cotizacionventa', raise_exception=True)
def cotizacion_detail(request, pk):
    cotizacion = get_object_or_404(CotizacionVenta, pk=pk)
    return render(request, 'ventas/cotizacion/cotizacion_detail.html', {
        'cotizacion': cotizacion
    })


@login_required
@permission_required('ventas.change_cotizacionventa', raise_exception=True)
def cotizacion_enviar(request, pk):
    cotizacion = get_object_or_404(CotizacionVenta, pk=pk)
    if cotizacion.estado == 'borrador':
        cotizacion.estado = 'enviada'
        cotizacion.save()
        messages.success(request, "Cotización enviada al cliente.")
    return redirect('ventas:cotizacion_detail', pk=pk)


@login_required
@permission_required('ventas.change_cotizacionventa', raise_exception=True)
def cotizacion_aceptar(request, pk):
    cotizacion = get_object_or_404(CotizacionVenta, pk=pk)
    if cotizacion.estado == 'enviada':
        cotizacion.estado = 'aceptada'
        cotizacion.save()
        messages.success(request, "Cotización aceptada por el cliente.")
    return redirect('ventas:cotizacion_detail', pk=pk)


@login_required
@permission_required('ventas.add_pedidoventa', raise_exception=True)
def cotizacion_convertir_pedido(request, pk):
    cotizacion = get_object_or_404(CotizacionVenta, pk=pk)

    if cotizacion.estado != 'aceptada':
        messages.error(request, "Solo se pueden convertir cotizaciones aceptadas.")
        return redirect('ventas:cotizacion_detail', pk=pk)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Crear pedido
                pedido = PedidoVenta.objects.create(
                    cliente=cotizacion.cliente,
                    cotizacion=cotizacion,
                    creado_por=request.user,
                    total=cotizacion.total
                )

                # Crear detalles del pedido
                for detalle_cot in cotizacion.detalles.all():
                    DetallePedido.objects.create(
                        pedido=pedido,
                        material=detalle_cot.material,
                        cantidad_solicitada=detalle_cot.cantidad,
                        precio_unitario=detalle_cot.precio_unitario,
                        descuento=detalle_cot.descuento,
                        subtotal=detalle_cot.subtotal
                    )

                # Actualizar estado de la cotización
                cotizacion.estado = 'convertida'
                cotizacion.save()

                messages.success(request, f"Pedido {pedido.id} creado desde la cotización {cotizacion.id}.")
                return redirect('ventas:pedido_detail', pk=pedido.pk)
        except Exception as e:
            messages.error(request, f"Error al convertir a pedido: {str(e)}")

    return render(request, 'ventas/cotizacion/cotizacion_confirm_convertir.html', {
        'cotizacion': cotizacion
    })

# PEDIDOS

@login_required
@permission_required('ventas.view_pedidoventa', raise_exception=True)
def pedido_list(request):
    pedidos = PedidoVenta.objects.select_related('cliente', 'cotizacion').all().order_by('-fecha')
    return render(request, 'ventas/pedido/pedido_list.html', {
        'pedidos': pedidos
    })


@login_required
@permission_required('ventas.add_pedidoventa', raise_exception=True)
def pedido_create(request):
    if request.method == 'POST':
        form = PedidoVentaForm(request.POST)
        formset = DetallePedidoFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    pedido = form.save(commit=False)
                    pedido.creado_por = request.user
                    pedido.save()

                    detalles = formset.save(commit=False)
                    for detalle in detalles:
                        detalle.pedido = pedido
                        detalle.save()
                    for detalle in formset.deleted_objects:
                        detalle.delete()

                    total = sum(detalle.subtotal for detalle in pedido.detalles.all())
                    pedido.total = total
                    pedido.save()

                    messages.success(request, f"Pedido {pedido.id} creado exitosamente.")
                    return redirect('ventas:pedido_detail', pk=pedido.pk)
            except Exception as e:
                messages.error(request, f"Error al crear el pedido: {str(e)}")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = PedidoVentaForm()
        formset = DetallePedidoFormSet(
            queryset=DetallePedido.objects.none(),
            initial=[{'descuento': 0}]
        )

    clientes = Cliente.objects.filter(activo=True)
    # Cargar todas las cotizaciones aceptadas para el modal
    cotizaciones = CotizacionVenta.objects.filter(estado='aceptada').select_related('cliente')
    materiales = Material.objects.filter(activo=True, es_inventariable=True)

    return render(request, 'ventas/pedido/pedido_form.html', {
        'form': form,
        'formset': formset,
        'empty_form': formset.empty_form,
        'clientes': clientes,
        'cotizaciones': cotizaciones,
        'materiales': materiales,
        'object': None,
    })

@login_required
@permission_required('ventas.view_pedidoventa', raise_exception=True)
def pedido_detail(request, pk):
    pedido = get_object_or_404(PedidoVenta, pk=pk)
    return render(request, 'ventas/pedido/pedido_detail.html', {
        'pedido': pedido
    })


@login_required
@permission_required('ventas.change_pedidoventa', raise_exception=True)
def pedido_confirmar(request, pk):
    pedido = get_object_or_404(PedidoVenta, pk=pk)

    if pedido.estado != 'borrador':
        messages.error(request, "Solo se pueden confirmar pedidos en borrador.")
        return redirect('ventas:pedido_detail', pk=pk)

    if request.method == 'POST':
        pedido.estado = 'confirmado'
        pedido.save()
        messages.success(request, f"Pedido {pedido.id} confirmado.")
        return redirect('ventas:pedido_detail', pk=pk)

    return render(request, 'ventas/pedido/pedido_confirm_confirmar.html', {
        'pedido': pedido
    })


@login_required
@permission_required('ventas.change_pedidoventa', raise_exception=True)
def pedido_surtir(request, pk):
    pedido = get_object_or_404(PedidoVenta, pk=pk)

    if pedido.estado != 'confirmado':
        messages.error(request, "Solo se pueden surtir pedidos confirmados.")
        return redirect('ventas:pedido_detail', pk=pk)

    # Obtener almacenes para el template
    from materiales.models import Almacen
    almacenes = Almacen.objects.filter(activo=True)

    # Verificar stock disponible
    faltante = []
    for detalle in pedido.detalles.all():
        if detalle.material.es_inventariable:
            stock_total = detalle.material.stocks.aggregate(
                total=Sum('cantidad')
            )['total'] or 0

            if stock_total < detalle.cantidad_solicitada:
                faltante.append({
                    'material': detalle.material,
                    'solicitado': detalle.cantidad_solicitada,
                    'disponible': stock_total
                })

    if faltante:
        messages.error(request, "No hay suficiente stock para surtir el pedido.")
        return render(request, 'ventas/pedido/pedido_surtir_stock_insuficiente.html', {
            'pedido': pedido,
            'faltante': faltante
        })

    if request.method == 'POST':
        almacen_id = request.POST.get('almacen_id')
        if not almacen_id:
            messages.error(request, "Debe seleccionar un almacén para el surtido.")
            return render(request, 'ventas/pedido/pedido_confirm_surtir.html', {
                'pedido': pedido,
                'almacenes': almacenes
            })

        try:
            from .utils import surtir_pedido
            # ✅ PASAR EL ALMACÉN SELECCIONADO
            factura = surtir_pedido(pedido, request.user, almacen_id)
            messages.success(request, f"Pedido surtido y facturado como {factura.folio}.")
            return redirect('ventas:factura_detail', pk=factura.pk)
        except Exception as e:
            messages.error(request, f"Error al surtir el pedido: {str(e)}")

    return render(request, 'ventas/pedido/pedido_confirm_surtir.html', {
        'pedido': pedido,
        'almacenes': almacenes  # ✅ Pasar almacenes al template
    })

@login_required
@permission_required('ventas.change_pedidoventa', raise_exception=True)
def pedido_surtir2(request, pk):
    pedido = get_object_or_404(PedidoVenta, pk=pk)

    if pedido.estado != 'confirmado':
        messages.error(request, "Solo se pueden surtir pedidos confirmados.")
        return redirect('ventas:pedido_detail', pk=pk)

    # Verificar stock disponible
    faltante = []
    for detalle in pedido.detalles.all():
        if detalle.material.es_inventariable:
            stock_total = detalle.material.stocks.aggregate(
                total=Sum('cantidad')
            )['total'] or 0

            if stock_total < detalle.cantidad_solicitada:
                faltante.append({
                    'material': detalle.material,
                    'solicitado': detalle.cantidad_solicitada,
                    'disponible': stock_total
                })

    if faltante:
        messages.error(request, "No hay suficiente stock para surtir el pedido.")
        return render(request, 'ventas/pedido/pedido_surtir_stock_insuficiente.html', {
            'pedido': pedido,
            'faltante': faltante
        })

    if request.method == 'POST':
        almacen_id = request.POST.get('almacen_id')
        try:
            from .utils import surtir_pedido
            factura = surtir_pedido(pedido, request.user, almacen_id)
            messages.success(request, f"Pedido surtido y facturado como {factura.folio}.")
            return redirect('ventas:factura_detail', pk=factura.pk)
        except Exception as e:
            messages.error(request, f"Error al surtir el pedido: {str(e)}")

    return render(request, 'ventas/pedido/pedido_confirm_surtir.html', {
        'pedido': pedido
    })

@login_required
@permission_required('ventas.add_pedidoventa', raise_exception=True)
def get_cotizaciones_cliente(request):
    """API para obtener cotizaciones por cliente (usado con AJAX)."""
    cliente_id = request.GET.get('cliente_id')
    if cliente_id:
        cotizaciones = CotizacionVenta.objects.filter(
            estado='aceptada',
            cliente_id=cliente_id
        ).select_related('cliente')

        data = []
        for cot in cotizaciones:
            data.append({
                'id': cot.id,
                'cliente_nombre': cot.cliente.nombre,
                'fecha': cot.fecha.strftime('%d/%m/%Y'),
                'total': float(cot.total),
                'folio': f"COT-{cot.id}"
            })

        return JsonResponse({'cotizaciones': data})
    return JsonResponse({'cotizaciones': []})

@login_required
def get_detalles_cotizacion(request, pk):
    """API para obtener los detalles de una cotización."""
    cotizacion = get_object_or_404(CotizacionVenta, pk=pk)
    detalles = []

    for detalle in cotizacion.detalles.all():
        detalles.append({
            'material_id': detalle.material.id,
            'material_nombre': f"{detalle.material.codigo} - {detalle.material.nombre}",
            'cantidad': float(detalle.cantidad),
            'precio_unitario': float(detalle.precio_unitario),
            'descuento': float(detalle.descuento),
        })

    return JsonResponse({'detalles': detalles})

# FACTURAS
@login_required
@permission_required('ventas.view_facturaventa', raise_exception=True)
def factura_list(request):
    facturas = FacturaVenta.objects.select_related('cliente', 'pedido').all().order_by('-fecha')
    return render(request, 'ventas/factura/factura_list.html', {
        'facturas': facturas
    })


@login_required
@permission_required('ventas.add_facturaventa', raise_exception=True)
def factura_create(request):
    if request.method == 'POST':
        form = FacturaVentaForm(request.POST)
        formset = DetalleFacturaFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    factura = form.save(commit=False)
                    factura.creado_por = request.user
                    factura.save()

                    detalles = formset.save(commit=False)
                    for detalle in detalles:
                        detalle.factura = factura
                        detalle.save()
                    for detalle in formset.deleted_objects:
                        detalle.delete()

                    # Calcular totales
                    subtotal = sum(detalle.subtotal for detalle in factura.detalles.all())
                    iva = sum(detalle.iva_monto for detalle in factura.detalles.all())
                    factura.subtotal = subtotal
                    factura.iva = iva
                    factura.total = subtotal + iva
                    factura.save()

                    # Crear Cuenta por Cobrar
                    CuentaPorCobrar.objects.create(
                        factura=factura,
                        cliente=factura.cliente,
                        monto_total=factura.total,
                        saldo_pendiente=factura.total,
                        fecha_vencimiento=factura.fecha  # Ajustar según política
                    )

                    messages.success(request, f"Factura {factura.folio} creada exitosamente.")
                    return redirect('ventas:factura_detail', pk=factura.pk)
            except Exception as e:
                messages.error(request, f"Error al crear la factura: {str(e)}")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = FacturaVentaForm()
        formset = DetalleFacturaFormSet(
            queryset=DetalleFactura.objects.none(),
            initial=[{'descuento': 0, 'iva_porcentaje': 16.00}]
        )

    clientes = Cliente.objects.filter(activo=True)
    pedidos = PedidoVenta.objects.filter(estado='completo')
    materiales = Material.objects.filter(activo=True, es_inventariable=True)

    return render(request, 'ventas/factura/factura_form.html', {
        'form': form,
        'formset': formset,
        'empty_form': formset.empty_form,
        'clientes': clientes,
        'pedidos': pedidos,
        'materiales': materiales,
        'object': None,
    })


@login_required
@permission_required('ventas.view_facturaventa', raise_exception=True)
def factura_detail(request, pk):
    factura = get_object_or_404(FacturaVenta, pk=pk)
    return render(request, 'ventas/factura/factura_detail.html', {
        'factura': factura
    })


@login_required
@permission_required('ventas.view_facturaventa', raise_exception=True)
def factura_print(request, pk):
    factura = get_object_or_404(FacturaVenta, pk=pk)
    return render(request, 'ventas/factura/factura_print.html', {
        'factura': factura
    })

# Cuentas por Pagar

@login_required
@permission_required('ventas.view_cuentaporcobrar', raise_exception=True)
def cxc_list(request):
    cxcs = CuentaPorCobrar.objects.select_related('factura__cliente', 'cliente').all().order_by('-fecha_creacion')
    return render(request, 'ventas/cxc/cxc_list.html', {
        'cxcs': cxcs
    })

@login_required
@permission_required('ventas.view_cuentaporcobrar', raise_exception=True)
def cxc_detail(request, pk):
    cxc = get_object_or_404(CuentaPorCobrar, pk=pk)
    total_pagado = cxc.pagos.aggregate(total=Sum('monto'))['total'] or 0

    return render(request, 'ventas/cxc/cxc_detail.html', {
        'cxc': cxc,
        'total_pagado': total_pagado
    })


@login_required
@permission_required('ventas.add_pagocuentaporcobrar', raise_exception=True)
def registrar_pago_cxc(request, cxc_id):
    cxc = get_object_or_404(CuentaPorCobrar, id=cxc_id)

    if cxc.estado == 'pagado':
        messages.error(request, "Esta cuenta ya ha sido pagada completamente.")
        return redirect('ventas:cxc_detail', pk=cxc.id)

    if request.method == 'POST':
        form = PagoCuentaPorCobrarForm(request.POST)
        if form.is_valid():
            try:
                pago = form.save(commit=False)  # ← No guardar aún
                pago.cuenta_por_cobrar = cxc  # ← Asignar la relación
                pago.creado_por = request.user
                pago.save()

                # CREAR MOVIMIENTO BANCARIO DE INGRESO
                MovimientoBancario.objects.create(
                    cuenta_bancaria=form.cleaned_data['cuenta_bancaria'],
                    tipo_movimiento='ingreso',
                    monto=pago.monto,
                    fecha=pago.fecha_pago,
                    descripcion=f"Cobro de cliente: {cxc.cliente.nombre}",
                    referencia=pago.referencia,
                    tipo_documento='cobro_cliente',
                    documento_id=cxc.id,
                    documento_numero=cxc.factura.folio,
                    creado_por=request.user,
                )

                messages.success(request, f"Pago de ${pago.monto} registrado exitosamente.")
                return redirect('ventas:cxc_detail', pk=cxc.id)
            except Exception as e:
                messages.error(request, f"Error al registrar el pago: {str(e)}")
    else:
        form = PagoCuentaPorCobrarForm()

    return render(request, 'ventas/cxc/pago_cxc_form.html', {
        'form': form,
        'cxc': cxc
    })

# REPORTES CXC
@login_required
@permission_required('ventas.view_cuentaporcobrar', raise_exception=True)
def reporte_cxc_saldos(request):
    today = date.today()

    cxcs = CuentaPorCobrar.objects.filter(
        saldo_pendiente__gt=0
    ).select_related(
        'factura__cliente', 'cliente'
    ).order_by('-fecha_creacion')

    # Calcular días vencidos en Python
    for cxc in cxcs:
        if cxc.fecha_vencimiento < today:
            cxc.dias_vencidos = (today - cxc.fecha_vencimiento).days
        else:
            cxc.dias_vencidos = 0

    total_saldo = cxcs.aggregate(total=Sum('saldo_pendiente'))['total'] or 0

    return render(request, 'ventas/cxc/reportes/cxc_saldos.html', {
        'cxcs': cxcs,
        'total_saldo': total_saldo,
        'today': today,
    })


@login_required
@permission_required('ventas.view_cuentaporcobrar', raise_exception=True)
def reporte_cxc_aging(request):
    """Reporte de antigüedad de saldos (Aging)."""
    today = date.today()

    # Obtener todas las CxC con saldo pendiente
    cxcs = CuentaPorCobrar.objects.filter(
        saldo_pendiente__gt=0
    ).select_related(
        'factura__cliente', 'cliente'
    ).order_by('fecha_vencimiento')

    # Calcular días vencidos en Python y agrupar por rangos
    rango_1_30 = []
    rango_31_60 = []
    rango_61_90 = []
    rango_90_mas = []

    for cxc in cxcs:
        if cxc.fecha_vencimiento < today:
            dias_vencidos = (today - cxc.fecha_vencimiento).days
        else:
            dias_vencidos = 0

        cxc.dias_vencidos = dias_vencidos

        if 1 <= dias_vencidos <= 30:
            rango_1_30.append(cxc)
        elif 31 <= dias_vencidos <= 60:
            rango_31_60.append(cxc)
        elif 61 <= dias_vencidos <= 90:
            rango_61_90.append(cxc)
        elif dias_vencidos > 90:
            rango_90_mas.append(cxc)

    # Calcular totales
    total_1_30 = sum(cxc.saldo_pendiente for cxc in rango_1_30)
    total_31_60 = sum(cxc.saldo_pendiente for cxc in rango_31_60)
    total_61_90 = sum(cxc.saldo_pendiente for cxc in rango_61_90)
    total_90_mas = sum(cxc.saldo_pendiente for cxc in rango_90_mas)

    total_general = total_1_30 + total_31_60 + total_61_90 + total_90_mas

    return render(request, 'ventas/cxc/reportes/cxc_aging.html', {
        'rango_1_30': rango_1_30,
        'rango_31_60': rango_31_60,
        'rango_61_90': rango_61_90,
        'rango_90_mas': rango_90_mas,
        'total_1_30': total_1_30,
        'total_31_60': total_31_60,
        'total_61_90': total_61_90,
        'total_90_mas': total_90_mas,
        'total_general': total_general,
        'today': today,
    })


@login_required
@permission_required('ventas.view_cuentaporcobrar', raise_exception=True)
def reporte_cxc_vencimientos(request):
    """Reporte de vencimientos próximos (próximos 30 días)."""
    today = date.today()
    fecha_hasta = today + timedelta(days=30)

    cxcs = CuentaPorCobrar.objects.filter(
        saldo_pendiente__gt=0,
        fecha_vencimiento__lte=fecha_hasta
    ).select_related(
        'factura__cliente', 'cliente'
    ).order_by('fecha_vencimiento')

    total_monto = cxcs.aggregate(total=Sum('monto_total'))['total'] or 0
    total_saldo = cxcs.aggregate(total=Sum('saldo_pendiente'))['total'] or 0

    return render(request, 'ventas/cxc/reportes/cxc_vencimientos.html', {
        'cxcs': cxcs,
        'fecha_hasta': fecha_hasta,
        'total_monto': total_monto,
        'total_saldo': total_saldo,
        'today': today,
    })


@login_required
@permission_required('ventas.view_cuentaporcobrar', raise_exception=True)
def reporte_cxc_clientes_mayor_saldo(request):
    """Reporte de clientes con mayor saldo pendiente."""
    clientes_saldo = Cliente.objects.filter(
        cuentaporcobrar__saldo_pendiente__gt=0
    ).annotate(
        saldo_total=Sum('cuentaporcobrar__saldo_pendiente')
    ).order_by('-saldo_total')

    # Calcular el número de facturas pendientes por cliente
    for cliente in clientes_saldo:
        cliente.facturas_pendientes = CuentaPorCobrar.objects.filter(
            cliente=cliente,
            saldo_pendiente__gt=0
        ).count()

    total_general = clientes_saldo.aggregate(total=Sum('saldo_total'))['total'] or 0

    return render(request, 'ventas/cxc/reportes/cxc_clientes_mayor_saldo.html', {
        'clientes_saldo': clientes_saldo,
        'total_general': total_general,
    })