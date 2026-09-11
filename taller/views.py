import json
import openpyxl

from openpyxl.utils import get_column_letter
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, OuterRef, Subquery
from django.utils import timezone
from .models import Mecanico, Vehiculo, OrdenServicio, ItemOrdenServicio, PagoOrdenServicio, VehiculoInventario
from materiales.models import MovimientoAlmacen, DetalleMovimientoAlmacen, StockAlmacen
from .forms import MecanicoForm, VehiculoForm, OrdenServicioForm, ItemOrdenServicioForm, PagoOrdenServicioForm, VehiculoInventarioForm
from django.db import transaction
from datetime import datetime, timedelta


@login_required
def dashboard_taller(request):
    """Dashboard principal del taller con resumen de órdenes activas"""

    # Conteos por estado
    ordenes_nuevas = OrdenServicio.objects.filter(estado=OrdenServicio.ESTADO_NUEVA).count()
    ordenes_diagnostico = OrdenServicio.objects.filter(estado=OrdenServicio.ESTADO_EN_DIAGNOSTICO).count()
    ordenes_cotizadas = OrdenServicio.objects.filter(estado=OrdenServicio.ESTADO_COTIZADA).count()
    ordenes_aprobadas = OrdenServicio.objects.filter(estado=OrdenServicio.ESTADO_APROBADA).count()
    ordenes_reparacion = OrdenServicio.objects.filter(estado=OrdenServicio.ESTADO_EN_REPARACION).count()
    ordenes_terminadas = OrdenServicio.objects.filter(estado=OrdenServicio.ESTADO_TERMINADA).count()

    # Órdenes activas (excluyendo entregadas, canceladas y rechazadas)
    estados_activos = [
        OrdenServicio.ESTADO_NUEVA,
        OrdenServicio.ESTADO_EN_DIAGNOSTICO,
        OrdenServicio.ESTADO_COTIZADA,
        OrdenServicio.ESTADO_APROBADA,
        OrdenServicio.ESTADO_EN_REPARACION,
        OrdenServicio.ESTADO_TERMINADA,
    ]

    ordenes_activas = OrdenServicio.objects.filter(estado__in=estados_activos).select_related(
        'cliente', 'vehiculo', 'mecanico_responsable'
    ).order_by('-fecha_entrada')

    # Estadísticas del mes actual
    hoy = timezone.now()
    primer_dia_mes = hoy.replace(day=1)

    estadisticas_mes = OrdenServicio.objects.filter(
        fecha_entrada__gte=primer_dia_mes
    ).aggregate(
        total_ordenes=Count('id'),
        ingresos_totales=Sum('total'),
        ordenes_entregadas=Count('id', filter=Q(estado=OrdenServicio.ESTADO_ENTREGADA))
    )

    context = {
        'ordenes_nuevas': ordenes_nuevas,
        'ordenes_diagnostico': ordenes_diagnostico,
        'ordenes_cotizadas': ordenes_cotizadas,
        'ordenes_aprobadas': ordenes_aprobadas,
        'ordenes_reparacion': ordenes_reparacion,
        'ordenes_terminadas': ordenes_terminadas,
        'ordenes_activas': ordenes_activas,
        'estadisticas_mes': estadisticas_mes,
        'menu_template': 'core/menus/menu_taller.html',
    }
    return render(request, 'taller/dashboard.html', context)

@login_required
def lista_ordenes(request):
    """Lista de todas las órdenes de servicio con filtros"""

    estado_filter = request.GET.get('estado', '')
    mecanico_filter = request.GET.get('mecanico', '')
    tipo_filter = request.GET.get('tipo', '')

    ordenes = OrdenServicio.objects.select_related(
        'cliente', 'vehiculo', 'mecanico_responsable'
    ).order_by('-fecha_entrada')

    if estado_filter:
        ordenes = ordenes.filter(estado=estado_filter)
    if mecanico_filter:
        ordenes = ordenes.filter(mecanico_responsable_id=mecanico_filter)
    if tipo_filter:
        ordenes = ordenes.filter(tipo_servicio=tipo_filter)

    mecanicos = Mecanico.objects.filter(activo=True)

    context = {
        'ordenes': ordenes,
        'mecanicos': mecanicos,
        'estados': OrdenServicio.ESTADOS_ORDEN,
        'tipos_servicio': OrdenServicio.TIPOS_SERVICIO,
        'estado_filter': estado_filter,
        'mecanico_filter': mecanico_filter,
        'tipo_filter': tipo_filter,
        'menu_template': 'core/menus/menu_taller.html',

    }

    return render(request,'taller/lista_ordenes.html', context)

@login_required
def detalle_orden(request, pk):
    """Detalle completo de una orden de servicio"""

    orden = get_object_or_404(
        OrdenServicio.objects.select_related('cliente', 'vehiculo', 'mecanico_responsable'),
        pk=pk
    )

    items = orden.items.all().order_by('tipo', 'descripcion')
    saldo_pendiente = orden.total - orden.total_pagado

    context = {
        'orden': orden,
        'items': items,
        'saldo_pendiente': saldo_pendiente,
        'menu_template': 'core/menus/menu_taller.html',

    }

    return render(request,'taller/detalle_orden.html', context)


@login_required
def crear_orden(request):
    """Crear una nueva orden de servicio (cliente o interna)"""

    if request.method == 'POST':
        form = OrdenServicioForm(request.POST)
        if form.is_valid():
            orden = form.save(commit=False)

            # Lógica para órdenes internas vs normales
            if orden.es_interna:
                # Si es interna, limpiar campos de cliente y vehículo de cliente
                orden.cliente = None
                orden.vehiculo = None
            else:
                # Si es normal, limpiar el vehículo de inventario
                orden.vehiculo_inventario = None

            orden.save()
            messages.success(request, f'Orden de servicio {orden.numero_os} creada exitosamente.')
            return redirect('taller:detalle_orden', pk=orden.pk)
    else:
        form = OrdenServicioForm()

    context = {
        'form': form,
        'titulo': 'Nueva Orden de Servicio',
        'menu_template': 'core/menus/menu_taller.html',
    }

    return render(request, 'taller/form_orden.html', context)


@login_required
def editar_orden(request, pk):
    """Editar una orden de servicio existente"""

    orden = get_object_or_404(OrdenServicio, pk=pk)

    # 🔒 BLOQUEO DE SEGURIDAD
    if orden.estado == OrdenServicio.ESTADO_ENTREGADA:
        messages.error(request, 'No se puede modificar una orden que ya ha sido entregada.')
        return redirect('taller:detalle_orden', pk=orden.pk)

    if request.method == 'POST':
        form = OrdenServicioForm(request.POST, instance=orden)
        if form.is_valid():
            orden = form.save(commit=False)

            # Lógica para órdenes internas vs normales
            if orden.es_interna:
                orden.cliente = None
                orden.vehiculo = None
            else:
                orden.vehiculo_inventario = None

            orden.save()
            messages.success(request, f'Orden {orden.numero_os} actualizada exitosamente.')
            return redirect('taller:detalle_orden', pk=orden.pk)
    else:
        form = OrdenServicioForm(instance=orden)

    context = {
        'form': form,
        'orden': orden,
        'titulo': f'Editar Orden {orden.numero_os}',
        'menu_template': 'core/menus/menu_taller.html',
    }

    return render(request, 'taller/form_orden.html', context)

@login_required
def cambiar_estado_orden(request, pk, nuevo_estado):
    """Cambiar el estado de una orden de servicio y generar movimiento de almacén si se entrega"""

    orden = get_object_or_404(OrdenServicio, pk=pk)

    # Validar transiciones permitidas
    transiciones_validas = {
        OrdenServicio.ESTADO_NUEVA: [OrdenServicio.ESTADO_EN_DIAGNOSTICO, OrdenServicio.ESTADO_CANCELADA],
        OrdenServicio.ESTADO_EN_DIAGNOSTICO: [OrdenServicio.ESTADO_COTIZADA,
                                              OrdenServicio.ESTADO_DIAGNOSTICO_RECHAZADO],
        OrdenServicio.ESTADO_COTIZADA: [OrdenServicio.ESTADO_APROBADA, OrdenServicio.ESTADO_COTIZACION_RECHAZADA],
        OrdenServicio.ESTADO_APROBADA: [OrdenServicio.ESTADO_EN_REPARACION],
        OrdenServicio.ESTADO_EN_REPARACION: [OrdenServicio.ESTADO_TERMINADA],
        OrdenServicio.ESTADO_TERMINADA: [OrdenServicio.ESTADO_ENTREGADA],
    }

    if nuevo_estado not in transiciones_validas.get(orden.estado, []):
        messages.error(request, 'Transición de estado no válida.')
        return redirect('taller:detalle_orden', pk=orden.pk)

    # Si el nuevo estado es ENTREGADA, crear movimiento de almacén
    if nuevo_estado == OrdenServicio.ESTADO_ENTREGADA:
        # Obtener ítems inventariables con material y almacén asignado
        items_con_material = orden.items.filter(
            tipo__in=[ItemOrdenServicio.TIPO_REFACCION, ItemOrdenServicio.TIPO_MATERIAL],
            material__isnull=False,
            almacen__isnull=False,
            material__es_inventariable=True
        ).select_related('material', 'almacen')

        if not items_con_material.exists():
            # Si no hay materiales que descontar, solo cambiar estado
            orden.estado = nuevo_estado
            orden.fecha_salida = timezone.now()
            orden.save()
            messages.success(request, f'Orden {orden.numero_os} entregada exitosamente (sin materiales que descontar).')
            return redirect('taller:detalle_orden', pk=orden.pk)

        # Agrupar ítems por almacén (un movimiento por almacén)
        items_por_almacen = {}
        for item in items_con_material:
            almacen_id = item.almacen.id
            if almacen_id not in items_por_almacen:
                items_por_almacen[almacen_id] = {
                    'almacen': item.almacen,
                    'items': []
                }
            items_por_almacen[almacen_id]['items'].append(item)

        try:
            with transaction.atomic():
                # Cambiar estado de la orden
                orden.estado = nuevo_estado
                orden.fecha_salida = timezone.now()
                orden.save()

                # Crear un movimiento por cada almacén
                for almacen_id, datos in items_por_almacen.items():
                    # Crear el movimiento de almacén
                    movimiento = MovimientoAlmacen.objects.create(
                        tipo='salida_taller',
                        almacen_origen=datos['almacen'],
                        documento_referencia=orden.numero_os,
                        notas=f"Consumo por Orden de Servicio {orden.numero_os} - Cliente: {orden.cliente} - Vehículo: {orden.vehiculo}",
                        estado='borrador',
                        creado_por=request.user
                    )

                    # Crear los detalles del movimiento
                    for item in datos['items']:
                        DetalleMovimientoAlmacen.objects.create(
                            movimiento=movimiento,
                            material=item.material,
                            cantidad=item.cantidad,
                            costo_unitario=item.precio_unitario,
                            referencia=item.descripcion
                        )

                    # Confirmar el movimiento (esto actualiza el stock automáticamente)
                    movimiento.confirmar(request.user)

                messages.success(
                    request,
                    f'✅ Orden {orden.numero_os} entregada. Se generaron {len(items_por_almacen)} movimiento(s) de almacén y el stock fue actualizado.'
                )

        except ValueError as e:
            messages.error(request, f'❌ Error al descontar stock: {str(e)}')
        except Exception as e:
            messages.error(request, f'❌ Error inesperado al procesar la entrega: {str(e)}')

        return redirect('taller:detalle_orden', pk=orden.pk)

    # Para otros estados, solo cambiar el estado
    orden.estado = nuevo_estado
    orden.save()
    messages.success(request, f'Estado de orden {orden.numero_os} cambiado a {orden.get_estado_display()}.')

    return redirect('taller:detalle_orden', pk=orden.pk)


@login_required
def agregar_item(request, pk):
    """Agregar un ítem (refacción/material/mano de obra) a una orden"""

    orden = get_object_or_404(OrdenServicio, pk=pk)

    # 🔒 BLOQUEO DE SEGURIDAD
    if orden.estado == OrdenServicio.ESTADO_ENTREGADA:
        messages.error(request, 'No se pueden agregar ítems a una orden ya entregada.')
        return redirect('taller:detalle_orden', pk=orden.pk)

    if request.method == 'POST':
        form = ItemOrdenServicioForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.orden_servicio = orden
            item.save()

            # Recalcular totales de la orden
            orden.subtotal_refacciones = orden.items.filter(
                tipo=ItemOrdenServicio.TIPO_REFACCION
            ).aggregate(total=Sum('subtotal'))['total'] or 0

            orden.subtotal_mano_obra = orden.items.filter(
                tipo=ItemOrdenServicio.TIPO_MANO_OBRA
            ).aggregate(total=Sum('subtotal'))['total'] or 0

            orden.total = orden.subtotal_refacciones + orden.subtotal_mano_obra - orden.descuento
            orden.save()

            messages.success(request, 'Ítem agregado exitosamente.')
            return redirect('taller:detalle_orden', pk=orden.pk)
    else:
        form = ItemOrdenServicioForm()

    context = {
        'form': form,
        'orden': orden,
        'menu_template': 'core/menus/menu_taller.html',
    }

    return render(request,'taller/form_item.html', context)

@login_required
def eliminar_item(request, pk_item):
    """Eliminar un ítem de una orden"""

    item = get_object_or_404(ItemOrdenServicio, pk=pk_item)
    orden = item.orden_servicio

    # 🔒 BLOQUEO DE SEGURIDAD
    if orden.estado == OrdenServicio.ESTADO_ENTREGADA:
        messages.error(request, 'No se pueden eliminar ítems de una orden ya entregada.')
        return redirect('taller:detalle_orden', pk=orden.pk)

    if request.method == 'POST':
        item.delete()

        # Recalcular totales de la orden
        orden.subtotal_refacciones = orden.items.filter(
            tipo=ItemOrdenServicio.TIPO_REFACCION
        ).aggregate(total=Sum('subtotal'))['total'] or 0

        orden.subtotal_mano_obra = orden.items.filter(
            tipo=ItemOrdenServicio.TIPO_MANO_OBRA
        ).aggregate(total=Sum('subtotal'))['total'] or 0

        orden.total = orden.subtotal_refacciones + orden.subtotal_mano_obra - orden.descuento
        orden.save()

        messages.success(request, 'Ítem eliminado exitosamente.')

    return redirect('taller:detalle_orden', pk=orden.pk)


# CRUD de Mecánicos
@login_required
def lista_mecanicos(request):
    """Lista de mecánicos"""
    mecanicos = Mecanico.objects.all().order_by('apellido', 'nombre')
    context = {
        'mecanicos': mecanicos,
        'menu_template': 'core/menus/menu_taller.html',
    }
    return render(request,'taller/lista_mecanicos.html', context)

@login_required
def crear_mecanico(request):
    """Crear un nuevo mecánico"""
    if request.method == 'POST':
        form = MecanicoForm(request.POST)
        if form.is_valid():
            mecanico = form.save()
            messages.success(request, f'Mecánico {mecanico.nombre_completo} creado exitosamente.')
            return redirect('taller:lista_mecanicos')
    else:
        form = MecanicoForm()

    context = {
        'form': form,
        'titulo': 'Nuevo Mecánico',
        'menu_template': 'core/menus/menu_taller.html',
    }
    return render(request,'taller/form_mecanico.html', context)

@login_required
def editar_mecanico(request, pk):
    """Editar un mecánico existente"""
    mecanico = get_object_or_404(Mecanico, pk=pk)

    if request.method == 'POST':
        form = MecanicoForm(request.POST, instance=mecanico)
        if form.is_valid():
            mecanico = form.save()
            messages.success(request, f'Mecánico {mecanico.nombre_completo} actualizado exitosamente.')
            return redirect('taller:lista_mecanicos')
    else:
        form = MecanicoForm(instance=mecanico)

    context = {
        'form': form,
        'mecanico': mecanico,
        'titulo': 'Editar Mecánico',
        'menu_template': 'core/menus/menu_taller.html',
    }
    return render(request,'taller/form_mecanico.html', context)

# CRUD de Vehículos
@login_required
def lista_vehiculos(request):
    """Lista de vehículos"""
    vehiculos = Vehiculo.objects.select_related('cliente').all().order_by('-fecha_creacion')
    context = {
        'vehiculos': vehiculos,
        'menu_template': 'core/menus/menu_taller.html',
    }
    return render(request,'taller/lista_vehiculos.html', context)

@login_required
def crear_vehiculo(request):
    """Crear un nuevo vehículo"""
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            vehiculo = form.save()
            messages.success(request, f'Vehículo {vehiculo} creado exitosamente.')
            return redirect('taller:lista_vehiculos')
    else:
        form = VehiculoForm()

    context = {
        'form': form,
        'titulo': 'Nuevo Vehículo',
        'menu_template': 'core/menus/menu_taller.html'
    }

    return render(request, 'taller/form_vehiculo.html', context)

@login_required
def editar_vehiculo(request, pk):
    """Editar un vehículo existente"""
    vehiculo = get_object_or_404(Vehiculo, pk=pk)

    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            vehiculo = form.save()
            messages.success(request, f'Vehículo {vehiculo} actualizado exitosamente.')
            return redirect('taller:lista_vehiculos')
    else:
        form = VehiculoForm(instance=vehiculo)

    context = {
        'form': form,
        'vehiculo': vehiculo,
        'titulo': 'Editar Vehículo',
        'menu_template': 'core/menus/menu_taller.html',
    }
    return render(request,'taller/form_vehiculo.html', context)

@login_required
def buscar_productos(request):
    """Búsqueda AJAX de materiales del inventario con información de almacenes"""
    query = request.GET.get('q', '')

    if len(query) < 2:
        return JsonResponse({'materiales': []})

    from materiales.models import Material

    materiales = Material.objects.filter(
        Q(nombre__icontains=query) |
        Q(codigo__icontains=query) |
        Q(descripcion__icontains=query)
    ).filter(activo=True)[:15]

    resultados = []
    for mat in materiales:
        # Obtener stock por almacén
        stocks = StockAlmacen.objects.filter(material=mat, almacen__activo=True)

        almacenes_con_stock = []
        stock_total = 0

        for stock in stocks:
            if stock.cantidad > 0:
                almacenes_con_stock.append({
                    'id': stock.almacen.id,
                    'nombre': stock.almacen.nombre,
                    'cantidad': float(stock.cantidad)
                })
                stock_total += float(stock.cantidad)

        resultados.append({
            'id': mat.id,
            'codigo': mat.codigo,
            'nombre': mat.nombre,
            'precio_unitario': float(mat.precio_unitario),
            'stock_total': stock_total,
            'almacenes': almacenes_con_stock,
            'es_inventariable': mat.es_inventariable,
            'unidad_medida': mat.get_unidad_medida_display()
        })

    return JsonResponse({'materiales': resultados})


@login_required
def vehiculos_por_cliente(request, cliente_id):
    """API AJAX para obtener vehículos de un cliente"""
    from clientes.models import Cliente  # Ajusta la importación según tu estructura

    vehiculos = Vehiculo.objects.filter(cliente_id=cliente_id).order_by('-año')

    resultados = []
    for veh in vehiculos:
        resultados.append({
            'id': veh.id,
            'marca': veh.marca,
            'modelo': veh.modelo,
            'año': veh.año,
            'placa': veh.placa or ''
        })

    return JsonResponse({'vehiculos': resultados})

@login_required
def registrar_pago(request, pk):
    """Registrar un pago parcial o total para una orden de servicio"""
    orden = get_object_or_404(OrdenServicio, pk=pk)

    # Solo permitir pagos si la orden está Entregada o Pagada (para abonos pendientes)
    if orden.estado not in [OrdenServicio.ESTADO_ENTREGADA, OrdenServicio.ESTADO_PAGADA]:
        messages.error(request, 'Solo se pueden registrar pagos en órdenes que ya han sido entregadas.')
        return redirect('taller:detalle_orden', pk=orden.pk)

    if request.method == 'POST':
        form = PagoOrdenServicioForm(request.POST)
        if form.is_valid():
            pago = form.save(commit=False)
            pago.orden_servicio = orden
            pago.creado_por = request.user
            pago.save()

            # Recalcular el total pagado de la orden
            total_pagado = orden.pagos.aggregate(Sum('monto'))['monto__sum'] or 0
            orden.total_pagado = total_pagado
            orden.save()

            # Si el pago cubre el total, cambiar el estado a PAGADA
            if orden.total_pagado >= orden.total:
                orden.estado = OrdenServicio.ESTADO_PAGADA
                orden.save()
                messages.success(request,
                                 f'✅ Pago registrado. ¡La orden {orden.numero_os} ha sido PAGADA completamente!')
            else:
                saldo_pendiente = orden.total - orden.total_pagado
                messages.success(request, f'✅ Pago registrado. Saldo pendiente: ${saldo_pendiente:.2f}')

            return redirect('taller:detalle_orden', pk=orden.pk)
    else:
        # Sugerir el saldo pendiente como monto por defecto
        saldo_pendiente = orden.total - orden.total_pagado
        form = PagoOrdenServicioForm(initial={'monto': saldo_pendiente})

    context = {
        'form': form,
        'orden': orden,
        'saldo_pendiente': saldo_pendiente,
        'titulo': f'Registrar Pago - Orden {orden.numero_os}',
        'menu_template': 'core/menus/menu_taller.html',

    }

    return render(request, 'taller/form_pago.html', context)


@login_required
def reporte_servicios(request):
    """Reporte de servicios por rango de fechas con análisis financiero"""

    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    cliente_id = request.GET.get('cliente', '')

    # Queryset base
    ordenes = OrdenServicio.objects.select_related('cliente', 'vehiculo').all()

    # Aplicar filtros
    if fecha_inicio:
        ordenes = ordenes.filter(fecha_entrada__date__gte=fecha_inicio)  # <-- Agregado __date
    if fecha_fin:
        ordenes = ordenes.filter(fecha_entrada__date__lte=fecha_fin)     # <-- Agregado __date
    if cliente_id:
        ordenes = ordenes.filter(cliente_id=cliente_id)

    # Calcular totales
    total_general = ordenes.aggregate(Sum('total'))['total__sum'] or 0
    total_pagado = ordenes.filter(estado=OrdenServicio.ESTADO_PAGADA).aggregate(Sum('total_pagado'))[
                       'total_pagado__sum'] or 0
    total_pendiente = ordenes.exclude(estado=OrdenServicio.ESTADO_PAGADA).aggregate(Sum('total'))['total__sum'] or 0

    # Desglose por metodo de pago
    pagos_por_metodo = {}
    for metodo in dict(PagoOrdenServicio.METODOS_PAGO):
        total_metodo = PagoOrdenServicio.objects.filter(
            orden_servicio__in=ordenes,
            metodo_pago=metodo
        ).aggregate(Sum('monto'))['monto__sum'] or 0
        if total_metodo > 0:
            pagos_por_metodo[metodo] = total_metodo

    # Clientes para el filtro
    from clientes.models import Cliente
    clientes = Cliente.objects.all().order_by('nombre')

    context = {
        'ordenes': ordenes,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'cliente_id': cliente_id,
        'clientes': clientes,
        'total_general': total_general,
        'total_pagado': total_pagado,
        'total_pendiente': total_pendiente,
        'pagos_por_metodo': pagos_por_metodo,
        'menu_template': 'core/menus/menu_taller.html',

    }

    return render(request, 'taller/reporte_servicios.html', context)


@login_required
def reporte_servicios_excel(request):
    """Exportar reporte de servicios a Excel"""

    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    cliente_id = request.GET.get('cliente', '')

    ordenes = OrdenServicio.objects.select_related('cliente', 'vehiculo').all()

    if fecha_inicio:
        ordenes = ordenes.filter(fecha_entrada__gte=fecha_inicio)
    if fecha_fin:
        ordenes = ordenes.filter(fecha_entrada__lte=fecha_fin)
    if cliente_id:
        ordenes = ordenes.filter(cliente_id=cliente_id)

    # Crear libro de Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Servicios"

    # Encabezados
    headers = [
        'No. OS', 'Fecha Entrada', 'Cliente', 'Vehículo',
        'Tipo Servicio', 'Estado', 'Total', 'Total Pagado', 'Saldo'
    ]
    ws.append(headers)

    # Datos
    for orden in ordenes:
        ws.append([
            orden.numero_os,
            orden.fecha_entrada.strftime('%d/%m/%Y'),
            str(orden.cliente),
            str(orden.vehiculo),
            orden.get_tipo_servicio_display(),
            orden.get_estado_display(),
            float(orden.total),
            float(orden.total_pagado),
            float(orden.total - orden.total_pagado)
        ])

    # Formatear columnas
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',

    )
    response[
        'Content-Disposition'] = f'attachment; filename="reporte_servicios_{datetime.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)

    return response


@login_required
def reporte_ejecutivo(request):
    """Dashboard Ejecutivo con KPIs del Taller"""
    from django.db.models import Count, Sum

    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)

    # 1. KPIs del Mes Actual
    ordenes_mes = OrdenServicio.objects.filter(fecha_entrada__date__gte=primer_dia_mes)
    total_ordenes_mes = ordenes_mes.count()

    # CORRECCIÓN: Solo órdenes de clientes (no internas) para ingresos
    ordenes_mes_clientes = ordenes_mes.filter(es_interna=False)
    ingresos_mes = ordenes_mes_clientes.aggregate(Sum('total'))['total__sum'] or 0
    cobrado_mes = ordenes_mes_clientes.aggregate(Sum('total_pagado'))['total_pagado__sum'] or 0

    # 2. Pendiente de Cobro (Global) - SOLO órdenes de clientes
    ordenes_pendientes = OrdenServicio.objects.filter(
        es_interna=False
    ).exclude(estado=OrdenServicio.ESTADO_PAGADA)
    total_pendiente = sum((orden.total - orden.total_pagado) for orden in ordenes_pendientes)
    count_pendiente = ordenes_pendientes.count()

    # 3. Tiempo Promedio de Reparación (Días) - INCLUYE órdenes internas (sí cuentan para productividad)
    ordenes_entregadas = OrdenServicio.objects.filter(
        estado__in=[OrdenServicio.ESTADO_ENTREGADA, OrdenServicio.ESTADO_PAGADA],
        fecha_salida__isnull=False
    )
    dias_reparacion = []
    for orden in ordenes_entregadas:
        dias = (orden.fecha_salida - orden.fecha_entrada).days
        dias_reparacion.append(dias)
    tiempo_promedio = round(sum(dias_reparacion) / len(dias_reparacion), 1) if dias_reparacion else 0

    # 4. Top Mecánico (con más órdenes) - INCLUYE órdenes internas (sí trabajan en ellas)
    top_mecanico_data = OrdenServicio.objects.values('mecanico_responsable').annotate(
        total_ordenes=Count('id')
    ).order_by('-total_ordenes').first()

    top_mecanico = None
    if top_mecanico_data and top_mecanico_data['mecanico_responsable']:
        from .models import Mecanico
        try:
            mecanico = Mecanico.objects.get(pk=top_mecanico_data['mecanico_responsable'])
            top_mecanico = {
                'nombre': str(mecanico),  # Usa el __str__ del modelo
                'total_ordenes': top_mecanico_data['total_ordenes']
            }
        except Mecanico.DoesNotExist:
            pass

    # 5. Top 5 Clientes - CORRECCIÓN: Solo órdenes con cliente real (no internas)
    top_clientes = OrdenServicio.objects.filter(
        es_interna=False,
        cliente__isnull=False
    ).values('cliente__nombre', 'cliente__id').annotate(
        total_ordenes=Count('id'),
        total_gastado=Sum('total')
    ).order_by('-total_ordenes')[:5]

    # 6. Tipos de Servicio más solicitados - INCLUYE órdenes internas (sí son servicios realizados)
    tipos_servicio = OrdenServicio.objects.values('tipo_servicio').annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')

    # 7. KPI de Órdenes Internas (Reparaciones de Inventario)
    ordenes_internas_mes = ordenes_mes.filter(es_interna=True)
    total_ordenes_internas = ordenes_internas_mes.count()
    costo_total_reparaciones_internas = ordenes_internas_mes.aggregate(
        Sum('total')
    )['total__sum'] or 0

    # Motos en reparación actualmente (internas no terminadas)
    motos_en_reparacion = OrdenServicio.objects.filter(
        es_interna=True
    ).exclude(
        estado__in=[OrdenServicio.ESTADO_ENTREGADA, OrdenServicio.ESTADO_PAGADA, OrdenServicio.ESTADO_CANCELADA]
    ).count()

    context = {
        'total_ordenes_mes': total_ordenes_mes,
        'ingresos_mes': ingresos_mes,
        'cobrado_mes': cobrado_mes,
        'total_pendiente': total_pendiente,
        'count_pendiente': count_pendiente,
        'tiempo_promedio': tiempo_promedio,
        'top_mecanico': top_mecanico,
        'top_clientes': top_clientes,
        'tipos_servicio': tipos_servicio,
        'total_ordenes_internas': total_ordenes_internas,
        'costo_total_reparaciones_internas': costo_total_reparaciones_internas,
        'motos_en_reparacion': motos_en_reparacion,
        'menu_template': 'core/menus/menu_taller.html',
    }

    return render(request, 'taller/reporte_ejecutivo.html', context)

@login_required
def reporte_clientes_inactivos(request):
    """Reporte de clientes que no han traído sus vehículos en un periodo determinado"""
    from clientes.models import Cliente
    # Filtro de días (por defecto 90 días)
    dias_inactividad = int(request.GET.get('dias', 90))
    fecha_limite = timezone.now().date() - timedelta(days=dias_inactividad)

    # Subconsulta para obtener la fecha de la última orden de cada cliente
    ultima_orden_subquery = OrdenServicio.objects.filter(
        cliente=OuterRef('pk')
    ).order_by('-fecha_entrada')

    # Obtener clientes y anotar su última visita y gasto histórico
    clientes_inactivos = Cliente.objects.annotate(
        ultima_visita=Subquery(ultima_orden_subquery.values('fecha_entrada__date')[:1]),
        total_historico=Sum('ordenes_servicio__total')  # <-- Cambiado a 'ordenes_servicio'
    ).filter(
        Q(ultima_visita__lt=fecha_limite) | Q(ultima_visita__isnull=True)
    ).order_by('ultima_visita')

    context = {
        'clientes': clientes_inactivos,
        'dias_inactividad': dias_inactividad,
        'fecha_limite': fecha_limite,
        'total_clientes_inactivos': clientes_inactivos.count(),
        'menu_template': 'core/menus/menu_taller.html',

    }

    return render(request, 'taller/reporte_clientes_inactivos.html', context)


from decimal import Decimal


@login_required
def imprimir_orden(request, pk):
    """Vista para generar la hoja de impresión de la orden de servicio"""
    orden = get_object_or_404(OrdenServicio, pk=pk)

    # Separamos los ítems para mostrarlos en sus respectivas tablas
    items_refacciones = orden.items.filter(tipo__in=[ItemOrdenServicio.TIPO_REFACCION, ItemOrdenServicio.TIPO_MATERIAL])
    items_mano_obra = orden.items.filter(tipo=ItemOrdenServicio.TIPO_MANO_OBRA)

    # Calcular IVA (16% sobre el subtotal antes de descuento)
    subtotal_antes_descuento = orden.subtotal_refacciones + orden.subtotal_mano_obra + orden.costo_diagnostico
    iva = round(subtotal_antes_descuento * Decimal('0.16'), 2)  # <-- Usar Decimal en lugar de float

    context = {
        'orden': orden,
        'items_refacciones': items_refacciones,
        'items_mano_obra': items_mano_obra,
        'iva': iva,
    }

    return render(request, 'taller/orden_servicio_print.html', context)

# Vehiculos

@login_required
def inventario_vehiculos_list(request):
    """Lista todas las motos en el inventario"""
    vehiculos = VehiculoInventario.objects.all()
    context = {
        'vehiculos': vehiculos,
        'titulo': 'Inventario de Motos',
        'menu_template': 'core/menus/menu_taller.html'
    }
    return render(request, 'taller/inventario_vehiculos_list.html', context)


@login_required
def inventario_vehiculos_create(request):
    """Crea una nueva moto en el inventario"""
    if request.method == 'POST':
        form = VehiculoInventarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Moto agregada al inventario exitosamente.')
            return redirect('taller:inventario_vehiculos_list')
    else:
        form = VehiculoInventarioForm()

    return render(request, 'taller/inventario_vehiculos_form.html', {'form': form, 'titulo': 'Nueva Moto'})


@login_required
def inventario_vehiculos_update(request, pk):
    """Edita una moto existente en el inventario"""
    vehiculo = get_object_or_404(VehiculoInventario, pk=pk)
    if request.method == 'POST':
        form = VehiculoInventarioForm(request.POST, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Moto actualizada exitosamente.')
            return redirect('taller:inventario_vehiculos_list')
    else:
        form = VehiculoInventarioForm(instance=vehiculo)

    return render(request, 'taller/inventario_vehiculos_form.html', {'form': form, 'titulo': 'Editar Moto'})

@login_required
def inventario_vehiculos_delete(request, pk):
    """Elimina una moto del inventario"""
    vehiculo = get_object_or_404(VehiculoInventario, pk=pk)
    if request.method == 'POST':
        vehiculo.delete()
        messages.success(request, 'Moto eliminada del inventario exitosamente.')
        return redirect('taller:inventario_vehiculos_list')
    return render(request, 'taller/inventario_vehiculos_confirm_delete.html', {'vehiculo': vehiculo})
