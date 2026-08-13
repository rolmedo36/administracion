import pandas as pd
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from datetime import datetime
from .models import Cliente, ActividadCliente, DocumentoCliente
from ventas.models import Vendedor, FacturaVenta, CuentaPorCobrar, PedidoVenta, CotizacionVenta
from .forms import ClienteForm, ActividadClienteForm, DocumentoClienteForm
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import timedelta
from collections import defaultdict

@login_required
@permission_required('clientes.view_cliente', raise_exception=True)
def cliente_index(request):
    return render(request, 'clientes/cliente_index.html', {
        'titulo': 'Ventas',
        'menu_template': 'core/menus/menu_cxc.html',
    })

@login_required
@permission_required('clientes.add_cliente', raise_exception=True)
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.creado_por = request.user
            cliente.save()
            messages.success(request, f"Cliente {cliente.nombre} creado exitosamente.")
            return redirect('clientes:cliente_list')
    else:
        form = ClienteForm()
    return render(request, 'clientes/cliente_form.html', {
        'form': form,
        'menu_template': 'core/menus/menu_cxc.html',
    })

@login_required
@permission_required('clientes.change_cliente', raise_exception=True)
def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cliente {cliente.nombre} actualizado.")
            return redirect('clientes:cliente_list')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes/cliente_form.html', {
        'form': form,
        'menu_template': 'core/menus/menu_cxc.html',
    })


@login_required
def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    # 1. Actividades
    actividades = ActividadCliente.objects.filter(cliente=cliente).order_by('-fecha_creacion')

    # 2. Resumen Ejecutivo (con datos reales)
    hoy = timezone.now().date()
    anio_actual = hoy.year

    # Saldo CxC (facturas no pagadas)
    cxc_pendiente = CuentaPorCobrar.objects.filter(
        cliente=cliente,
        estado__in=['pendiente', 'parcial']
    ).aggregate(total=Sum('saldo_pendiente'))['total'] or 0

    # Crédito disponible
    limite = cliente.limite_credito or 0
    credito_disponible = max(0, limite - cxc_pendiente)

    # Última compra (factura activa/timbrada más reciente)
    ultima_factura = FacturaVenta.objects.filter(
        cliente=cliente,
        estado__in=['activa', 'timbrada']
    ).order_by('-fecha').first()

    # Total ventas año actual
    ventas_anio = FacturaVenta.objects.filter(
        cliente=cliente,
        estado__in=['activa', 'timbrada'],
        fecha__year=anio_actual
    ).aggregate(total=Sum('total'))['total'] or 0

    # Total facturas vencidas
    facturas_vencidas = CuentaPorCobrar.objects.filter(
        cliente=cliente,
        fecha_vencimiento__lt=hoy,
        estado__in=['pendiente', 'parcial']
    ).count()

    # 6. Datos para la Gráfica de Ventas (Últimos 12 meses)
    hoy = timezone.now().date()
    hace_12_meses = hoy - timedelta(days=365)

    # Consultar facturas activas o timbradas del último año
    facturas_ventas = FacturaVenta.objects.filter(
        cliente=cliente,
        estado__in=['activa', 'timbrada'],
        fecha__gte=hace_12_meses
    ).values('fecha__year', 'fecha__month').annotate(
        total_ventas=Sum('total')
    ).order_by('fecha__year', 'fecha__month')

    # Crear un diccionario para mapear los datos de la BD
    ventas_dict = defaultdict(float)
    for item in facturas_ventas:
        # La clave será "Año-Mes" (ej: 2024-7)
        key = f"{item['fecha__year']}-{item['fecha__month']}"
        ventas_dict[key] = item['total_ventas']

    # Generar las etiquetas (Meses) y los datos (Totales) para Chart.js
    meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    chart_labels = []
    chart_data = []

    # Recorremos los últimos 12 meses para asegurar que todos aparezcan (aunque sea con 0)
    for i in range(12):
        # Calcular el mes y año exacto
        mes_offset = i - 11  # De -11 a 0
        fecha_mes = hoy.replace(day=1) + timedelta(days=32 * mes_offset)
        fecha_mes = fecha_mes.replace(day=1)  # Normalizar al día 1

        year = fecha_mes.year
        month = fecha_mes.month

        key = f"{year}-{month}"
        chart_labels.append(f"{meses_nombres[month - 1]} {year}")
        chart_data.append(float(ventas_dict.get(key, 0)))

    resumen = {
        'limite_credito': limite,
        'saldo_cxc': cxc_pendiente,
        'credito_disponible': credito_disponible,
        'ultima_compra_fecha': ultima_factura.fecha if ultima_factura else None,
        'ultima_compra_monto': ultima_factura.total if ultima_factura else 0,
        'ultima_compra_folio': ultima_factura.folio if ultima_factura else '—',
        'total_ventas_anio': ventas_anio,
        'facturas_vencidas': facturas_vencidas,
    }

    # 3. Datos para pestaña CxC (con paginación)
    cxc_list = CuentaPorCobrar.objects.filter(cliente=cliente).order_by('-fecha_vencimiento')
    cxc_paginator = Paginator(cxc_list, 25)
    cxc_page = request.GET.get('cxc_page')
    cxc_paginated = cxc_paginator.get_page(cxc_page)

    # 4. Datos para pestaña Ventas (con paginación)
    ventas_list = FacturaVenta.objects.filter(cliente=cliente).order_by('-fecha')
    ventas_paginator = Paginator(ventas_list, 25)
    ventas_page = request.GET.get('ventas_page')
    ventas_paginated = ventas_paginator.get_page(ventas_page)

    # 5. Datos para pestaña Actividades (ya lo teníamos)
    actividades_paginator = Paginator(actividades, 50)
    actividades_page = request.GET.get('actividades_page')
    actividades_paginated = actividades_paginator.get_page(actividades_page)

    # 6. Datos para la Gráfica de Ventas (Últimos 12 meses)
    hoy = timezone.now().date()
    hace_12_meses = hoy - timedelta(days=365)

    # 7. Vehículos del cliente (del módulo Taller)
    from taller.models import Vehiculo, OrdenServicio
    vehiculos = Vehiculo.objects.filter(cliente=cliente).order_by('-año')

    # 8. Órdenes de servicio del cliente
    ordenes_servicio = OrdenServicio.objects.filter(cliente=cliente).select_related('vehiculo',
                                                                                    'mecanico_responsable').order_by(
        '-fecha_entrada')[:20]  # Últimas 20

    # Consultar facturas activas o timbradas del último año
    facturas_ventas = FacturaVenta.objects.filter(
        cliente=cliente,
        estado__in=['activa', 'timbrada'],
        fecha__gte=hace_12_meses
    ).values('fecha__year', 'fecha__month').annotate(
        total_ventas=Sum('total')
    ).order_by('fecha__year', 'fecha__month')

    # Crear un diccionario para mapear los datos de la BD
    ventas_dict = defaultdict(float)
    for item in facturas_ventas:
        # La clave será "Año-Mes" (ej: 2024-7)
        key = f"{item['fecha__year']}-{item['fecha__month']}"
        ventas_dict[key] = item['total_ventas']

    # Generar las etiquetas (Meses) y los datos (Totales) para Chart.js
    meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    chart_labels = []
    chart_data = []

    # Recorremos los últimos 12 meses para asegurar que todos aparezcan (aunque sea con 0)
    for i in range(12):
        # Calcular el mes y año exacto
        mes_offset = i - 11  # De -11 a 0
        fecha_mes = hoy.replace(day=1) + timedelta(days=32 * mes_offset)
        fecha_mes = fecha_mes.replace(day=1)  # Normalizar al día 1

        year = fecha_mes.year
        month = fecha_mes.month

        key = f"{year}-{month}"
        chart_labels.append(f"{meses_nombres[month - 1]} {year}")
        chart_data.append(float(ventas_dict.get(key, 0)))

    return render(request, 'clientes/cliente_detail.html', {
        'cliente': cliente,
        'actividades': actividades[:5],  # Solo últimas 5 para el resumen
        'actividades_paginated': actividades_paginated,  # Para la pestaña completa
        'resumen': resumen,
        'cxc_paginated': cxc_paginated,
        'ventas_paginated': ventas_paginated,
        'hoy': hoy,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'vehiculos': vehiculos,
        'ordenes_servicio': ordenes_servicio,
        'menu_template': 'core/menus/menu_cxc.html',

    })

@login_required
@permission_required('clientes.view_cliente', raise_exception=True)
def cliente_list(request):
    # Obtener queryset base
    clientes = Cliente.objects.all()

    # Filtro por vendedor si el usuario es vendedor
    if request.user.groups.filter(name='Vendedor').exists():
        try:
            vendedor = request.user.vendedor
            clientes = clientes.filter(vendedores_asignados=vendedor)
        except Vendedor.DoesNotExist:
            clientes = Cliente.objects.none()  # No tiene perfil de vendedor

    # Filtro por nombre
    nombre_query = request.GET.get('nombre', '')
    if nombre_query:
        clientes = clientes.filter(
            models.Q(nombre__icontains=nombre_query) |
            models.Q(nombre_comercial__icontains=nombre_query) |
            models.Q(codigo__icontains=nombre_query)
        )

    clientes = clientes.order_by('nombre')

    # Paginación
    paginator = Paginator(clientes, 25)  # 25 clientes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Exportar a Excel
    if request.GET.get('export') == 'excel':
        return exportar_clientes_excel(clientes)

    return render(request, 'clientes/cliente_list.html', {
        'page_obj': page_obj,
        'nombre_query': nombre_query,
        'menu_template': 'core/menus/menu_cxc.html',
    })


def exportar_clientes_excel(queryset):
    """Exporta la lista de clientes a Excel."""
    data = []
    for cliente in queryset:
        data.append({
            'Código': cliente.codigo,
            'Nombre': cliente.nombre,
            'Nombre Comercial': cliente.nombre_comercial,
            'Tipo': cliente.get_tipo_cliente_display(),
            'RFC': cliente.rfc,
            'Email': cliente.email,
            'Teléfono': cliente.telefono,
            'Ciudad': cliente.ciudad,
            'Estado': cliente.estado,
            'Límite Crédito': float(cliente.limite_credito),
            'Días Crédito': cliente.dias_credito,
            'Clasificación': cliente.get_clasificacion_display(),
            'Activo': 'Sí' if cliente.activo else 'No',
        })

    df = pd.DataFrame(data)

    # Crear respuesta HTTP
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=clientes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    # Escribir a Excel
    df.to_excel(response, index=False, sheet_name='Clientes')

    return response

@login_required
def crear_actividad_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        form = ActividadClienteForm(request.POST)
        if form.is_valid():
            # Guardamos sin commit aún para asignar el cliente y el usuario manualmente
            actividad = form.save(commit=False)
            actividad.cliente = cliente
            actividad.creado_por = request.user
            actividad.save()

            # Redirigimos de vuelta al detalle del cliente
            return redirect('clientes:cliente_detail', pk=cliente.pk)
    else:
        form = ActividadClienteForm()

    return render(request, 'clientes/crear_actividad.html', {
        'form': form,
        'cliente': cliente
    })

@login_required
@require_POST  # Seguridad: solo aceptamos peticiones POST para cambiar estados
def completar_tarea(request, actividad_id):
    actividad = get_object_or_404(ActividadCliente, pk=actividad_id, tipo='tarea')

    # Lógica de interruptor: si está pendiente la completamos, si no, la reabrimos
    if actividad.estado == 'pendiente':
        actividad.estado = 'completada'
    else:
        actividad.estado = 'pendiente'
    actividad.save()

    messages.success(request, "Estado de la tarea actualizado correctamente.")
    return redirect('clientes:cliente_detail', pk=actividad.cliente.pk)


@login_required
@require_POST
def cerrar_reunion(request, actividad_id):
    actividad = get_object_or_404(ActividadCliente, pk=actividad_id, tipo='evento')

    # 1. Marcar la reunión actual como completada
    actividad.estado = 'completada'
    actividad.save()

    # 2. Capturar datos del modal
    notas = request.POST.get('notas', '').strip()
    seguimiento_titulo = request.POST.get('seguimiento_titulo', '').strip()
    seguimiento_fecha = request.POST.get('seguimiento_fecha', '')
    seguimiento_tipo = request.POST.get('seguimiento_tipo', 'tarea')

    # 3. Crear un comentario automático con las notas de la reunión
    if notas:
        ActividadCliente.objects.create(
            cliente=actividad.cliente,
            tipo='comentario',
            titulo=f"Notas de reunión: {actividad.titulo}",
            descripcion=notas,
            es_privado=actividad.es_privado,
            creado_por=request.user
        )

    # 4. Crear la tarea o evento de seguimiento si se agendó uno
    if seguimiento_fecha and seguimiento_titulo:
        ActividadCliente.objects.create(
            cliente=actividad.cliente,
            tipo=seguimiento_tipo,
            titulo=seguimiento_titulo,
            fecha_programada=seguimiento_fecha,
            estado='pendiente',
            es_privado=actividad.es_privado,
            creado_por=request.user
        )

    messages.success(request, "Reunión cerrada. Notas y seguimiento registrados.")
    return redirect('clientes:cliente_detail', pk=actividad.cliente.pk)

@login_required
def subir_documento_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        form = DocumentoClienteForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.cliente = cliente
            documento.subido_por = request.user
            documento.save()

            messages.success(request, f"Documento '{documento.get_tipo_display()}' subido correctamente.")
            return redirect('clientes:cliente_detail', pk=cliente.pk)
        else:
            messages.error(request, "Error al subir el documento. Verifica el formato y tamaño.")
    else:
        form = DocumentoClienteForm()

    return render(request, 'clientes/subir_documento.html', {
        'form': form,
        'cliente': cliente,
    })