from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction
from .models import CotizacionVenta, PedidoVenta, DetallePedido, Cliente, Material, DetalleCotizacion
from .forms import CotizacionVentaForm, DetalleCotizacionFormSet


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