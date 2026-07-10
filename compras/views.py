from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.forms import modelformset_factory
from django.db import transaction
from .models import Proveedor, OrdenCompra, DetalleOrdenCompra, CuentaPorPagar, PagoCuentaPorPagar
from .forms import ProveedorForm, OrdenCompraForm, DetalleOrdenFormSet, RecepcionOrdenForm, PagoCuentaPorPagarForm
from materiales.models import Material
from datetime import date
import json
from flujocaja.models import MovimientoBancario

# === PROVEEDORES (mantenemos CBV o FBV, pero por consistencia usamos FBV) ===

@login_required
@permission_required('compras.view_proveedor', raise_exception=True)
def compras_index(request):
    return render(request, 'compras/compras_index.html', {
        'titulo': "Compras",
        'menu_template': 'core/menus/menu_cxp.html',
    })

@login_required
@permission_required('compras.view_proveedor', raise_exception=True)
def proveedor_list(request):
    proveedores = Proveedor.objects.all().order_by('nombre')
    return render(request, 'compras/proveedor_list.html', {
        'proveedores': proveedores,
        'menu_template': 'core/menus/menu_cxp.html',
    })


@login_required
@permission_required('compras.add_proveedor', raise_exception=True)
def proveedor_create(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.instance.creado_por = request.user
            form.save()
            messages.success(request, "Proveedor creado exitosamente.")
            return redirect('compras:proveedor_list')
    else:
        form = ProveedorForm()
    return render(request, 'compras/proveedor_form.html', {
        'form': form,
        'menu_template': 'core/menus/menu_cxp.html',
    })


@login_required
@permission_required('compras.change_proveedor', raise_exception=True)
def proveedor_update(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, "Proveedor actualizado.")
            return redirect('compras:proveedor_list')
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'compras/proveedor_form.html', {
        'form': form,
        'menu_template': 'core/menus/menu_cxp.html',
    })


@login_required
@permission_required('compras.delete_proveedor', raise_exception=True)
def proveedor_delete(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        messages.success(request, "Proveedor eliminado.")
        return redirect('compras:proveedor_list')
    return render(request, 'compras/proveedor_confirm_delete.html', {
        'object': proveedor,
        'menu_template': 'core/menus/menu_cxp.html',
    })


# === ORDENES DE COMPRA ===

@login_required
@permission_required('compras.view_ordencompra', raise_exception=True)
def ordencompra_list(request):
    ordenes = OrdenCompra.objects.select_related('proveedor').all().order_by('-fecha_creacion')
    return render(request, 'compras/ordencompra_list.html', {
        'ordenes': ordenes,
        'menu_template': 'core/menus/menu_cxp.html',
    })

@login_required
@permission_required('compras.view_ordencompra', raise_exception=True)
def ordencompra_detail(request, pk):
    orden = get_object_or_404(OrdenCompra, pk=pk)
    return render(request, 'compras/ordencompra_detail.html', {
        'orden': orden,
        'menu_template': 'core/menus/menu_cxp.html',
    })

@login_required
@permission_required('compras.add_ordencompra', raise_exception=True)
def ordencompra_create(request):
    if request.method == 'POST':
        form = OrdenCompraForm(request.POST)
        formset = DetalleOrdenFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    orden = form.save(commit=False)
                    orden.creado_por = request.user
                    orden.save()

                    detalles = formset.save(commit=False)
                    for detalle in detalles:
                        detalle.orden = orden
                        detalle.save()
                    for detalle in formset.deleted_objects:
                        detalle.delete()

                    total = sum(d.subtotal for d in orden.detalles.all())
                    orden.total = total
                    orden.save()

                    messages.success(request, f"Orden de compra {orden.numero} creada exitosamente.")
                    return redirect('compras:ordencompra_list')
            except Exception as e:
                messages.error(request, f"Error al guardar: {str(e)}")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = OrdenCompraForm()
        formset = DetalleOrdenFormSet(queryset=DetalleOrdenCompra.objects.none())

    proveedores = Proveedor.objects.filter(activo=True)
    materiales = Material.objects.filter(activo=True)
    materiales_data = {
        str(mat.id): {
            'aplica_iva': mat.aplica_iva
        }
        for mat in Material.objects.filter(activo=True)
    }

    return render(request, 'compras/ordencompra_form.html', {
        'form': form,
        'detalles': formset,
        'empty_form': formset.empty_form,
        'proveedores': proveedores,
        'materiales': materiales,
        'materiales_data_json': json.dumps(materiales_data),
        'object': None,
        'menu_template': 'core/menus/menu_cxp.html',
    })

@login_required
@permission_required('compras.change_ordencompra', raise_exception=True)
def ordencompra_update(request, pk):
    orden = get_object_or_404(OrdenCompra, pk=pk)
    if request.method == 'POST':
        form = OrdenCompraForm(request.POST, instance=orden)
        formset = DetalleOrdenFormSet(request.POST, instance=orden)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    orden = form.save(commit=False)
                    orden.full_clean()
                    formset.save()
                    total = sum(d.subtotal for d in orden.detalles.all())
                    orden.total = total
                    orden.save()
                    messages.success(request, f"Orden {orden.numero} actualizada.")
                    return redirect('compras:ordencompra_list')
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
        else:
            messages.error(request, "Corrija los errores.")
    else:
        form = OrdenCompraForm(instance=orden)
        formset = DetalleOrdenFormSet(instance=orden)

    proveedores = Proveedor.objects.filter(activo=True)
    materiales = Material.objects.filter(activo=True)
    materiales_data = {
        str(mat.id): {
            'aplica_iva': mat.aplica_iva
        }
        for mat in Material.objects.filter(activo=True)
    }

    return render(request, 'compras/ordencompra_form.html', {
        'form': form,
        'detalles': formset,
        'empty_form': formset.empty_form,
        'proveedores': proveedores,
        'materiales': materiales,
        'materiales_data_json': json.dumps(materiales_data),
        'object': orden,
        'menu_template': 'core/menus/menu_cxp.html',
    })


@login_required
@permission_required('compras.delete_ordencompra', raise_exception=True)
def ordencompra_delete(request, pk):
    orden = get_object_or_404(OrdenCompra, pk=pk)
    if request.method == 'POST':
        orden.delete()
        messages.success(request, "Orden eliminada.")
        return redirect('compras:ordencompra_list')
    return render(request, 'compras/ordencompra_confirm_delete.html', {
        'object': orden,
        'menu_template': 'core/menus/menu_cxp.html',
    })

@login_required
@permission_required('compras.view_ordencompra', raise_exception=True)
def ordenes_por_recibir(request):
    ordenes = OrdenCompra.objects.filter(estado='confirmada').select_related('proveedor').order_by('-fecha_creacion')
    return render(request, 'compras/ordencompra_list.html', {
        'ordenes': ordenes,
        'modo_recepcion': True,
        'menu_template': 'core/menus/menu_cxp.html',
    })

@login_required
@permission_required('compras.change_ordencompra', raise_exception=True)
def recepcion_orden(request, pk):
    orden = get_object_or_404(OrdenCompra, pk=pk)

    if orden.estado != 'confirmada':
        messages.error(request, "Solo se pueden recibir órdenes en estado 'Confirmada'.")
        return redirect('compras:ordencompra_detail', pk=pk)

    if request.method == 'POST':
        form = RecepcionOrdenForm(request.POST)
        if form.is_valid():
            try:
                referencia = form.cleaned_data['referencia']
                fecha_vencimiento = form.cleaned_data['fecha_vencimiento']
                almacen = form.cleaned_data['almacen']

                orden.recibir(request.user, referencia, fecha_vencimiento, almacen)
                messages.success(request, f"Orden {orden.numero} recibida y stock actualizado en {almacen.nombre}.")
                return redirect('compras:ordencompra_detail', pk=pk)
            except Exception as e:
                messages.error(request, f"Error al recibir la orden: {str(e)}")
    else:
        form = RecepcionOrdenForm()

    return render(request, 'compras/recepcion_orden.html', {
        'orden': orden,
        'form': form,
        'menu_template': 'core/menus/menu_cxp.html',
    })

# CXP
@login_required
@permission_required('compras.add_pagocuentaporpagar', raise_exception=True)
def registrar_pago_cxp(request, cxp_id):
    cxp = get_object_or_404(CuentaPorPagar, id=cxp_id)
    if request.method == 'POST':
        form = PagoCuentaPorPagarForm(request.POST, cxp=cxp)
        if form.is_valid():
            pago = form.save(commit=False)
            pago.cuenta_por_pagar = cxp
            pago.creado_por = request.user
            pago.save()

            # CREAR MOVIMIENTO BANCARIO DE EGRESO
            MovimientoBancario.objects.create(
                cuenta_bancaria=form.cleaned_data['cuenta_bancaria'],
                tipo_movimiento='egreso',
                monto=pago.monto,
                fecha=pago.fecha_pago,
                descripcion=f"Pago a proveedor: {cxp.proveedor.nombre}",
                referencia=pago.referencia,
                tipo_documento='pago_proveedor',
                documento_id=cxp.id,
                documento_numero=cxp.referencia,
                creado_por=request.user,
            )

            messages.success(request, f"Pago de ${pago.monto} registrado exitosamente.")
            return redirect('compras:detalle_cxp', cxp_id=cxp.id)
    else:
        form = PagoCuentaPorPagarForm(cxp=cxp)

    return render(request, 'compras/pago_cxp_form.html', {
        'form': form,
        'cxp': cxp,
        'menu_template': 'core/menus/menu_cxp.html',
    })


@login_required
@permission_required('compras.view_cuentaporpagar', raise_exception=True)
def detalle_cxp(request, cxp_id):
    cxp = get_object_or_404(CuentaPorPagar, id=cxp_id)
    total_pagado = cxp.pagos.aggregate(total=Sum('monto'))['total'] or 0
    return render(request, 'compras/cxp_detail.html', {
        'cxp': cxp,
        'total_pagado': total_pagado,
        'menu_template': 'core/menus/menu_cxp.html',
    })

# REPORTE CXP
@login_required
@permission_required('compras.view_cuentaporpagar', raise_exception=True)
def reporte_cxp(request):
    proveedores = Proveedor.objects.filter(activo=True).order_by('nombre')
    proveedor_id = request.GET.get('proveedor')

    cxps = CuentaPorPagar.objects.select_related('proveedor').order_by('fecha_vencimiento')

    if proveedor_id and proveedor_id != 'todos':
        cxps = cxps.filter(proveedor_id=proveedor_id)

    # Calcular días vencidos y preparar datos
    today = date.today()
    cxps_con_dias = []
    for cxp in cxps:
        dias_vencidos = (today - cxp.fecha_vencimiento).days
        cxp.dias_vencidos = max(dias_vencidos, 0)  # Si es negativo, 0
        cxps_con_dias.append(cxp)

    total_importe = cxps.aggregate(total=Sum('monto_total'))['total'] or 0
    total_saldo = cxps.aggregate(total=Sum('saldo_pendiente'))['total'] or 0

    return render(request, 'compras/reporte_cxp.html', {
        'cxps': cxps_con_dias,  # Ahora incluye .dias_vencidos
        'proveedores': proveedores,
        'proveedor_seleccionado': proveedor_id,
        'total_importe': total_importe,
        'total_saldo': total_saldo,
        'today': today,
        'menu_template': 'core/menus/menu_cxp.html',
    })

