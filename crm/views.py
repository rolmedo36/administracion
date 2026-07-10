from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg, F
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .services import enviar_email_actividad
from .models import Prospecto, Oportunidad, Actividad, PlantillaEmail
from .forms import ProspectoForm, OportunidadForm, ActividadForm, PlantillaEmailForm
from decimal import Decimal

@login_required
def crm_index(request):
    return render(request, 'crm/crm_index.html', {
        'titulo': 'CRM',
        'menu_template': 'core/menus/menu_crm.html',
    })

@login_required
@permission_required('crm.view_prospecto', raise_exception=True)
def prospecto_list(request):
    """Lista de prospectos con filtros."""
    prospectos = Prospecto.objects.filter(activo=True).select_related('asignado_a')

    # Filtros
    estado = request.GET.get('estado')
    origen = request.GET.get('origen')
    asignado = request.GET.get('asignado')
    search = request.GET.get('search')

    if estado:
        prospectos = prospectos.filter(estado=estado)
    if origen:
        prospectos = prospectos.filter(origen=origen)
    if asignado:
        prospectos = prospectos.filter(asignado_a=asignado)
    if search:
        prospectos = prospectos.filter(
            Q(nombre__icontains=search) |
            Q(empresa__icontains=search) |
            Q(email__icontains=search)
        )

    # Ordenar por próximo contacto
    prospectos = prospectos.order_by('fecha_proximo_contacto', '-fecha_creacion')

    # Opciones para filtros
    estados = Prospecto._meta.get_field('estado').choices
    origenes = Prospecto._meta.get_field('origen').choices
    comerciales = User.objects.filter(is_active=True)

    return render(request, 'crm/prospecto/prospecto_list.html', {
        'prospectos': prospectos,
        'estados': estados,
        'origenes': origenes,
        'comerciales': comerciales,
        'estado_filtro': estado,
        'origen_filtro': origen,
        'asignado_filtro': asignado,
        'search_query': search,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.add_prospecto', raise_exception=True)
def prospecto_create(request):
    """Crear nuevo prospecto."""
    if request.method == 'POST':
        form = ProspectoForm(request.POST)
        if form.is_valid():
            prospecto = form.save(commit=False)
            prospecto.creado_por = request.user
            # Si no se asigna comercial, asignar al creador
            if not prospecto.asignado_a:
                prospecto.asignado_a = request.user
            prospecto.save()
            messages.success(request, f"Prospecto {prospecto.nombre} creado exitosamente.")
            return redirect('crm:prospecto_detail', pk=prospecto.pk)
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = ProspectoForm()
        # Asignar por defecto al usuario actual
        form.fields['asignado_a'].initial = request.user

    return render(request, 'crm/prospecto/prospecto_form.html', {
        'form': form,
        'object': None,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.change_prospecto', raise_exception=True)
def prospecto_update(request, pk):
    """Editar prospecto existente."""
    prospecto = get_object_or_404(Prospecto, pk=pk, activo=True)
    if request.method == 'POST':
        form = ProspectoForm(request.POST, instance=prospecto)
        if form.is_valid():
            form.save()
            messages.success(request, f"Prospecto {prospecto.nombre} actualizado.")
            return redirect('crm:prospecto_detail', pk=prospecto.pk)
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = ProspectoForm(instance=prospecto)

    return render(request, 'crm/prospecto/prospecto_form.html', {
        'form': form,
        'object': prospecto,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.view_prospecto', raise_exception=True)
def prospecto_detail(request, pk):
    """Detalle de prospecto."""
    prospecto = get_object_or_404(Prospecto, pk=pk, activo=True)
    return render(request, 'crm/prospecto/prospecto_detail.html', {
        'prospecto': prospecto,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.delete_prospecto', raise_exception=True)
def prospecto_delete(request, pk):
    """Eliminar prospecto (desactivar)."""
    prospecto = get_object_or_404(Prospecto, pk=pk, activo=True)
    if request.method == 'POST':
        prospecto.activo = False
        prospecto.save()
        messages.success(request, f"Prospecto {prospecto.nombre} desactivado.")
        return redirect('crm:prospecto_list')
    return render(request, 'crm/prospecto/prospecto_confirm_delete.html', {
        'object': prospecto,
        'menu_template': 'core/menus/menu_crm.html',
    })

# OPORTUNIDADES

@login_required
@permission_required('crm.view_oportunidad', raise_exception=True)
def oportunidad_list(request):
    # Lista de oportunidades con filtros y pipeline.
    oportunidades = Oportunidad.objects.filter(activo=True).select_related(
        'prospecto', 'cliente', 'asignado_a'
    )

    # Filtros
    etapa = request.GET.get('etapa')
    asignado = request.GET.get('asignado')
    search = request.GET.get('search')

    if etapa:
        oportunidades = oportunidades.filter(etapa=etapa)
    if asignado:
        oportunidades = oportunidades.filter(asignado_a=asignado)
    if search:
        oportunidades = oportunidades.filter(
            Q(nombre__icontains=search) |
            Q(prospecto__nombre__icontains=search) |
            Q(cliente__nombre__icontains=search)
        )

    # Ordenar por prioridad (próximo contacto, luego fecha de cierre)
    oportunidades = oportunidades.order_by('fecha_proximo_contacto', 'fecha_cierre_estimada')

    # Estadísticas del pipeline
    pipeline_stats = oportunidades.values('etapa').annotate(
        total_oportunidades=Count('id'),
        monto_total=Sum('monto_estimado')
    ).order_by('etapa')

    # Opciones para filtros
    etapas = Oportunidad._meta.get_field('etapa').choices
    comerciales = User.objects.filter(is_active=True)

    return render(request, 'crm/oportunidad/oportunidad_list.html', {
        'oportunidades': oportunidades,
        'pipeline_stats': pipeline_stats,
        'etapas': etapas,
        'comerciales': comerciales,
        'etapa_filtro': etapa,
        'asignado_filtro': asignado,
        'search_query': search,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.add_oportunidad', raise_exception=True)
def oportunidad_create(request):
    # Crear nueva oportunidad.
    if request.method == 'POST':
        form = OportunidadForm(request.POST)
        if form.is_valid():
            oportunidad = form.save(commit=False)
            oportunidad.creado_por = request.user
            if not oportunidad.asignado_a:
                oportunidad.asignado_a = request.user
            oportunidad.save()
            messages.success(request, f"Oportunidad {oportunidad.nombre} creada exitosamente.")
            return redirect('crm:oportunidad_detail', pk=oportunidad.pk)
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = OportunidadForm()
        form.fields['asignado_a'].initial = request.user

    return render(request, 'crm/oportunidad/oportunidad_form.html', {
        'form': form,
        'object': None,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.change_oportunidad', raise_exception=True)
def oportunidad_update(request, pk):
    # Editar oportunidad existente.
    oportunidad = get_object_or_404(Oportunidad, pk=pk, activo=True)
    if request.method == 'POST':
        form = OportunidadForm(request.POST, instance=oportunidad)
        if form.is_valid():
            form.save()
            messages.success(request, f"Oportunidad {oportunidad.nombre} actualizada.")
            return redirect('crm:oportunidad_detail', pk=oportunidad.pk)
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = OportunidadForm(instance=oportunidad)

    return render(request, 'crm/oportunidad/oportunidad_form.html', {
        'form': form,
        'object': oportunidad,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.view_oportunidad', raise_exception=True)
def oportunidad_detail(request, pk):
    # Detalle de oportunidad.
    oportunidad = get_object_or_404(Oportunidad, pk=pk, activo=True)
    return render(request, 'crm/oportunidad/oportunidad_detail.html', {
        'oportunidad': oportunidad,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.delete_oportunidad', raise_exception=True)
def oportunidad_delete(request, pk):
    # Eliminar oportunidad (desactivar).
    oportunidad = get_object_or_404(Oportunidad, pk=pk, activo=True)
    if request.method == 'POST':
        oportunidad.activo = False
        oportunidad.save()
        messages.success(request, f"Oportunidad {oportunidad.nombre} desactivada.")
        return redirect('crm:oportunidad_list')
    return render(request, 'crm/oportunidad/oportunidad_confirm_delete.html', {
        'object': oportunidad,
        'menu_template': 'core/menus/menu_crm.html',
    })

# ACTIVIDADES

@login_required
@permission_required('crm.view_actividad', raise_exception=True)
def actividad_list(request):
    # Lista de actividades con filtros.
    actividades = Actividad.objects.select_related(
        'prospecto', 'oportunidad', 'relacionado_con', 'creado_por'
    )

    # Filtros
    tipo = request.GET.get('tipo')
    estado = request.GET.get('estado')
    relacionado = request.GET.get('relacionado')
    search = request.GET.get('search')

    # Por defecto, mostrar actividades pendientes y futuras
    if not estado:
        actividades = actividades.filter(
            Q(estado='pendiente') | Q(fecha_hora__gte=timezone.now())
        )
    else:
        actividades = actividades.filter(estado=estado)

    if tipo:
        actividades = actividades.filter(tipo=tipo)
    if relacionado:
        actividades = actividades.filter(relacionado_con=relacionado)
    if search:
        actividades = actividades.filter(
            Q(asunto__icontains=search) |
            Q(descripcion__icontains=search)
        )

    actividades = actividades.order_by('fecha_hora')

    # Opciones para filtros
    tipos = Actividad._meta.get_field('tipo').choices
    estados = Actividad._meta.get_field('estado').choices
    usuarios = User.objects.filter(is_active=True)

    return render(request, 'crm/actividad/actividad_list.html', {
        'actividades': actividades,
        'tipos': tipos,
        'estados': estados,
        'usuarios': usuarios,
        'tipo_filtro': tipo,
        'estado_filtro': estado,
        'relacionado_filtro': relacionado,
        'search_query': search,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.add_actividad', raise_exception=True)
def actividad_create(request):
    # Crear nueva actividad.
    if request.method == 'POST':
        form = ActividadForm(request.POST)
        if form.is_valid():
            actividad = form.save(commit=False)
            actividad.creado_por = request.user
            actividad.save()

            # Si es un email, enviarlo inmediatamente
            if actividad.tipo == 'email' and actividad.estado == 'completada':
                enviado = enviar_email_actividad(actividad)
                if not enviado:
                    messages.warning(request, "La actividad se creó pero no se pudo enviar el email.")

            messages.success(request, f"Actividad {actividad.asunto} creada exitosamente.")
            return redirect('crm:actividad_detail', pk=actividad.pk)
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = ActividadForm()
        # Asignar por defecto al usuario actual
        form.fields['relacionado_con'].initial = request.user

    return render(request, 'crm/actividad/actividad_form.html', {
        'form': form,
        'object': None,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.change_actividad', raise_exception=True)
def actividad_update(request, pk):
    # Editar actividad existente.
    actividad = get_object_or_404(Actividad, pk=pk)
    if request.method == 'POST':
        form = ActividadForm(request.POST, instance=actividad)
        if form.is_valid():
            form.save()
            messages.success(request, f"Actividad {actividad.asunto} actualizada.")
            return redirect('crm:actividad_detail', pk=actividad.pk)
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = ActividadForm(instance=actividad)

    return render(request, 'crm/actividad/actividad_form.html', {
        'form': form,
        'object': actividad,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.view_actividad', raise_exception=True)
def actividad_detail(request, pk):
    # Detalle de actividad.
    actividad = get_object_or_404(Actividad, pk=pk)
    return render(request, 'crm/actividad/actividad_detail.html', {
        'actividad': actividad,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.delete_actividad', raise_exception=True)
def actividad_delete(request, pk):
    # Eliminar actividad.
    actividad = get_object_or_404(Actividad, pk=pk)
    if request.method == 'POST':
        actividad.delete()
        messages.success(request, f"Actividad {actividad.asunto} eliminada.")
        return redirect('crm:actividad_list')
    return render(request, 'crm/actividad/actividad_confirm_delete.html', {
        'object': actividad,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.change_actividad', raise_exception=True)
def completar_actividad(request, pk):
    # Marcar actividad como completada.
    actividad = get_object_or_404(Actividad, pk=pk)
    if actividad.estado != 'completada':
        actividad.estado = 'completada'
        actividad.completada_fecha = timezone.now()
        actividad.save()

        # Si es un email, enviarlo al completar
        if actividad.tipo == 'email':
            enviado = enviar_email_actividad(actividad)
            if not enviado:
                messages.warning(request, "La actividad se completó pero no se pudo enviar el email.")

        messages.success(request, f"Actividad {actividad.asunto} completada.")

    return redirect('crm:actividad_detail', pk=pk)

# PLANTILLAS

@login_required
@permission_required('crm.view_plantillaemail', raise_exception=True)
def plantilla_email_list(request):
    # Lista de plantillas de email.
    plantillas = PlantillaEmail.objects.all().order_by('-fecha_creacion')

    # Filtros
    activa = request.GET.get('activa')
    categoria = request.GET.get('categoria')
    search = request.GET.get('search')

    if activa:
        plantillas = plantillas.filter(activa=(activa == 'true'))
    if categoria:
        plantillas = plantillas.filter(categoria__icontains=categoria)
    if search:
        plantillas = plantillas.filter(
            Q(nombre__icontains=search) |
            Q(asunto__icontains=search) |
            Q(categoria__icontains=search)
        )

    return render(request, 'crm/plantilla_email/plantilla_email_list.html', {
        'plantillas': plantillas,
        'activa_filtro': activa,
        'categoria_filtro': categoria,
        'search_query': search,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.add_plantillaemail', raise_exception=True)
def plantilla_email_create(request):
    # Crear nueva plantilla de email.
    if request.method == 'POST':
        form = PlantillaEmailForm(request.POST)
        if form.is_valid():
            plantilla = form.save(commit=False)
            plantilla.creado_por = request.user
            plantilla.save()
            messages.success(request, f"Plantilla {plantilla.nombre} creada exitosamente.")
            return redirect('crm:plantilla_email_detail', pk=plantilla.pk)
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = PlantillaEmailForm()

    return render(request, 'crm/plantilla_email/plantilla_email_form.html', {
        'form': form,
        'object': None,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.view_plantillaemail', raise_exception=True)
def plantilla_email_detail(request, pk):
    # Detalle de plantilla de email.
    plantilla = get_object_or_404(PlantillaEmail, pk=pk)
    return render(request, 'crm/plantilla_email/plantilla_email_detail.html', {
        'plantilla': plantilla,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.change_plantillaemail', raise_exception=True)
def plantilla_email_update(request, pk):
    # Editar plantilla de email.
    plantilla = get_object_or_404(PlantillaEmail, pk=pk)
    if request.method == 'POST':
        form = PlantillaEmailForm(request.POST, instance=plantilla)
        if form.is_valid():
            form.save()
            messages.success(request, f"Plantilla {plantilla.nombre} actualizada.")
            return redirect('crm:plantilla_email_detail', pk=plantilla.pk)
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = PlantillaEmailForm(instance=plantilla)

    return render(request, 'crm/plantilla_email/plantilla_email_form.html', {
        'form': form,
        'object': plantilla,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.delete_plantillaemail', raise_exception=True)
def plantilla_email_delete(request, pk):
    # Eliminar plantilla de email.
    plantilla = get_object_or_404(PlantillaEmail, pk=pk)
    if request.method == 'POST':
        plantilla.delete()
        messages.success(request, f"Plantilla {plantilla.nombre} eliminada.")
        return redirect('crm:plantilla_email_list')
    return render(request, 'crm/plantilla_email/plantilla_email_confirm_delete.html', {
        'object': plantilla,
        'menu_template': 'core/menus/menu_crm.html',
    })

# REPORTES

@login_required
@permission_required('crm.view_oportunidad', raise_exception=True)
def reporte_pipeline_ventas(request):
    # Reporte de pipeline de ventas.
    from .models import ETAPA_OPORTUNIDAD_CHOICES

    # Pipeline principal
    pipeline = Oportunidad.objects.filter(activo=True).values(
        'etapa'
    ).annotate(
        total_oportunidades=Count('id'),
        monto_total=Sum('monto_estimado'),
        probabilidad_promedio=Avg('probabilidad')
    ).order_by('etapa')

    # Valor ponderado (monto * probabilidad) y suma total
    valor_ponderado = Decimal('0')
    monto_total_pipeline = Decimal('0')  # ← Suma total para el footer
    pipeline_con_nombres = []

    for etapa in pipeline:
        monto_total = etapa['monto_total'] or Decimal('0')
        monto_total_pipeline += monto_total  # ← Acumular para el total

        if monto_total and etapa['probabilidad_promedio']:
            monto_decimal = Decimal(str(monto_total))
            probabilidad_decimal = Decimal(str(etapa['probabilidad_promedio']))
            valor_ponderado_etapa = monto_decimal * (probabilidad_decimal / Decimal('100'))
            valor_ponderado += valor_ponderado_etapa
        else:
            valor_ponderado_etapa = Decimal('0')

        # Agregar nombre de la etapa
        nombre_etapa = dict(ETAPA_OPORTUNIDAD_CHOICES).get(etapa['etapa'], etapa['etapa'])

        pipeline_con_nombres.append({
            'etapa': etapa['etapa'],
            'nombre_etapa': nombre_etapa,
            'total_oportunidades': etapa['total_oportunidades'],
            'monto_total': monto_total,
            'probabilidad_promedio': etapa['probabilidad_promedio'],
            'valor_ponderado': valor_ponderado_etapa,
            'tiempo_promedio': {
                'prospecto': 2,
                'contacto': 3,
                'necesidades': 5,
                'propuesta': 7,
                'negociacion': 10,
                'ganado': 0,
                'perdido': 0,
            }.get(etapa['etapa'], 0)
        })

    # Tiempo promedio en cada etapa
    tiempo_etapas = {
        'prospecto': 2,
        'contacto': 3,
        'necesidades': 5,
        'propuesta': 7,
        'negociacion': 10,
        'ganado': 0,
        'perdido': 0,
    }

    # Oportunidades ganadas recientes
    oportunidades_ganadas = Oportunidad.objects.filter(
        etapa='ganado',
        activo=True,
        fecha_creacion__gte=timezone.now() - timedelta(days=30)
    ).count()

    # Oportunidades perdidas recientes
    oportunidades_perdidas = Oportunidad.objects.filter(
        etapa='perdido',
        activo=True,
        fecha_creacion__gte=timezone.now() - timedelta(days=30)
    ).count()

    tasa_conversion = 0
    if oportunidades_ganadas + oportunidades_perdidas > 0:
        tasa_conversion = (oportunidades_ganadas / (oportunidades_ganadas + oportunidades_perdidas)) * 100

    return render(request, 'crm/reportes/pipeline_ventas.html', {
        'pipeline': pipeline_con_nombres,
        'valor_ponderado_total': valor_ponderado,
        'monto_total_pipeline': monto_total_pipeline,
        'tiempo_etapas': tiempo_etapas,
        'oportunidades_ganadas': oportunidades_ganadas,
        'oportunidades_perdidas': oportunidades_perdidas,
        'tasa_conversion': tasa_conversion,
        'menu_template': 'core/menus/menu_crm.html',
    })


@login_required
@permission_required('crm.view_prospecto', raise_exception=True)
def reporte_tasa_conversion(request):
    # Reporte de tasa de conversión.
    # Totales
    total_prospectos = Prospecto.objects.filter(activo=True).count()
    total_oportunidades = Oportunidad.objects.filter(activo=True).count()
    total_clientes = Oportunidad.objects.filter(etapa='ganado', activo=True).count()

    # Conversión general
    tasa_prospecto_oportunidad = 0
    tasa_oportunidad_cliente = 0
    tasa_prospecto_cliente = 0

    if total_prospectos > 0:
        tasa_prospecto_oportunidad = (total_oportunidades / total_prospectos) * 100
    if total_oportunidades > 0:
        tasa_oportunidad_cliente = (total_clientes / total_oportunidades) * 100
    if total_prospectos > 0:
        tasa_prospecto_cliente = (total_clientes / total_prospectos) * 100

    # Conversión por origen
    conversion_origen = Prospecto.objects.filter(activo=True).values(
        'origen'
    ).annotate(
        total_prospectos=Count('id'),
        total_oportunidades=Count('oportunidad'),
        total_clientes=Count('oportunidad__id', filter=Q(oportunidad__etapa='ganado'))
    )

    for origen in conversion_origen:
        origen['tasa_prospecto_oportunidad'] = 0
        origen['tasa_oportunidad_cliente'] = 0
        origen['tasa_prospecto_cliente'] = 0

        if origen['total_prospectos'] > 0:
            origen['tasa_prospecto_oportunidad'] = (origen['total_oportunidades'] / origen['total_prospectos']) * 100
        if origen['total_oportunidades'] > 0:
            origen['tasa_oportunidad_cliente'] = (origen['total_clientes'] / origen['total_oportunidades']) * 100
        if origen['total_prospectos'] > 0:
            origen['tasa_prospecto_cliente'] = (origen['total_clientes'] / origen['total_prospectos']) * 100

    return render(request, 'crm/reportes/tasa_conversion.html', {
        'total_prospectos': total_prospectos,
        'total_oportunidades': total_oportunidades,
        'total_clientes': total_clientes,
        'tasa_prospecto_oportunidad': tasa_prospecto_oportunidad,
        'tasa_oportunidad_cliente': tasa_oportunidad_cliente,
        'tasa_prospecto_cliente': tasa_prospecto_cliente,
        'conversion_origen': conversion_origen,
        'menu_template': 'core/menus/menu_crm.html',
    })

@login_required
@permission_required('crm.view_oportunidad', raise_exception=True)
def reporte_rendimiento_comercial(request):
    """Reporte de rendimiento por comercial."""
    from django.contrib.auth.models import User

    # Rendimiento por usuario
    rendimiento = User.objects.filter(
        is_active=True
    ).annotate(
        total_prospectos_asignados=Count('prospecto', distinct=True),
        total_oportunidades_asignadas=Count('oportunidad', distinct=True),
        total_oportunidades_ganadas=Count(
            'oportunidad',
            filter=Q(oportunidad__etapa='ganado'),
            distinct=True
        ),
        monto_pipeline=Sum('oportunidad__monto_estimado', distinct=True),
        monto_ganado=Sum(
            'oportunidad__monto_estimado',
            filter=Q(oportunidad__etapa='ganado'),
            distinct=True
        )
    ).filter(
        total_oportunidades_asignadas__gt=0
    )

    # Calcular tasas y promedios
    rendimiento_lista = []
    monto_maximo = Decimal('0')

    for comercial in rendimiento:
        comercial_dict = {
            'username': comercial.username,
            'total_prospectos_asignados': comercial.total_prospectos_asignados,
            'total_oportunidades_asignadas': comercial.total_oportunidades_asignadas,
            'total_oportunidades_ganadas': comercial.total_oportunidades_ganadas,
            'monto_pipeline': comercial.monto_pipeline or Decimal('0'),
            'monto_ganado': comercial.monto_ganado or Decimal('0'),
            'tasa_conversion': 0,
            'valor_promedio_oportunidad': Decimal('0'),
            'porcentaje_monto': 0  # ← Nuevo campo para el gráfico
        }

        if comercial.total_oportunidades_asignadas > 0:
            comercial_dict['tasa_conversion'] = (
                                                            comercial.total_oportunidades_ganadas / comercial.total_oportunidades_asignadas) * 100

        if comercial_dict['total_oportunidades_ganadas'] > 0 and comercial_dict['monto_ganado']:
            comercial_dict['valor_promedio_oportunidad'] = comercial_dict['monto_ganado'] / comercial_dict[
                'total_oportunidades_ganadas']

        # Encontrar el monto máximo para calcular porcentajes
        if comercial_dict['monto_ganado'] > monto_maximo:
            monto_maximo = comercial_dict['monto_ganado']

        rendimiento_lista.append(comercial_dict)

    # Calcular porcentajes para el gráfico
    for comercial in rendimiento_lista:
        if monto_maximo > 0:
            comercial['porcentaje_monto'] = (comercial['monto_ganado'] / monto_maximo) * 100
        else:
            comercial['porcentaje_monto'] = 0

    # Ordenar para el top 5
    top_comerciales = sorted(rendimiento_lista, key=lambda x: x['monto_ganado'], reverse=True)[:5]

    return render(request, 'crm/reportes/rendimiento_comercial.html', {
        'rendimiento': rendimiento_lista,
        'top_comerciales': top_comerciales,
        'menu_template': 'core/menus/menu_crm.html',
    })

@login_required
@permission_required('crm.view_actividad', raise_exception=True)
def reporte_actividades_seguimiento(request):
    """Reporte de actividades y seguimiento."""
    now = timezone.now()

    # Actividades por estado
    actividades_estado = Actividad.objects.values('estado').annotate(
        total=Count('id')
    )

    # Actividades por tipo
    actividades_tipo = Actividad.objects.values('tipo').annotate(
        total=Count('id')
    )

    # Actividades pendientes vencidas
    actividades_vencidas = Actividad.objects.filter(
        estado='pendiente',
        fecha_hora__lt=now
    ).count()

    # Actividades completadas en los últimos 30 días
    actividades_completadas = Actividad.objects.filter(
        estado='completada',
        completada_fecha__gte=now - timedelta(days=30)
    ).count()

    # Tiempo promedio de respuesta
    actividades_tiempo = Actividad.objects.filter(
        estado='completada',
        completada_fecha__isnull=False,
        fecha_creacion__isnull=False
    )

    tiempo_promedio_respuesta = 0
    if actividades_tiempo.exists():
        total_segundos = sum(
            (act.completada_fecha - act.fecha_creacion).total_seconds()
            for act in actividades_tiempo
        )
        tiempo_promedio_respuesta = total_segundos / actividades_tiempo.count() / 3600  # En horas

    # Actividades por comercial (usando la relación correcta)
    from django.contrib.auth.models import User
    actividades_comercial = User.objects.filter(
        is_active=True
    ).annotate(
        total_actividades=Count('actividades_programadas')
    ).filter(total_actividades__gt=0)

    return render(request, 'crm/reportes/actividades_seguimiento.html', {
        'actividades_estado': actividades_estado,
        'actividades_tipo': actividades_tipo,
        'actividades_vencidas': actividades_vencidas,
        'actividades_completadas': actividades_completadas,
        'tiempo_promedio_respuesta': tiempo_promedio_respuesta,
        'actividades_comercial': actividades_comercial,
        'menu_template': 'core/menus/menu_crm.html',
    })

@login_required
@permission_required('crm.view_prospecto', raise_exception=True)
def reporte_analisis_origen(request):
    # Reporte de análisis por origen de leads.
    from .models import ORIGEN_PROSPECTO_CHOICES

    # Análisis por origen
    analisis_origen = Prospecto.objects.filter(activo=True).values(
        'origen'
    ).annotate(
        total_prospectos=Count('id'),
        total_calificados=Count('id', filter=Q(estado='calificado')),
        total_oportunidades=Count('oportunidad'),
        total_clientes=Count('oportunidad__id', filter=Q(oportunidad__etapa='ganado'))
    )

    # Calcular tasas por origen y agregar nombres
    analisis_origen_lista = []
    for origen in analisis_origen:
        tasa_calificacion = 0
        tasa_oportunidad = 0
        tasa_cliente = 0

        if origen['total_prospectos'] > 0:
            tasa_calificacion = (origen['total_calificados'] / origen['total_prospectos']) * 100
            tasa_cliente = (origen['total_clientes'] / origen['total_prospectos']) * 100

        if origen['total_calificados'] > 0:
            tasa_oportunidad = (origen['total_oportunidades'] / origen['total_calificados']) * 100

        # Obtener el nombre legible del origen
        nombre_origen = dict(ORIGEN_PROSPECTO_CHOICES).get(origen['origen'], origen['origen'])

        analisis_origen_lista.append({
            'origen': origen['origen'],
            'nombre_origen': nombre_origen,
            'total_prospectos': origen['total_prospectos'],
            'total_calificados': origen['total_calificados'],
            'total_oportunidades': origen['total_oportunidades'],
            'total_clientes': origen['total_clientes'],
            'tasa_calificacion': tasa_calificacion,
            'tasa_oportunidad': tasa_oportunidad,
            'tasa_cliente': tasa_cliente,
        })

    # Origen más efectivo (mayor tasa de conversión a cliente)
    origen_efectivo = None
    if analisis_origen_lista:
        origen_efectivo = max(analisis_origen_lista, key=lambda x: x['tasa_cliente'])

    return render(request, 'crm/reportes/analisis_origen.html', {
        'analisis_origen': analisis_origen_lista,
        'origen_efectivo': origen_efectivo,
        'menu_template': 'core/menus/menu_crm.html',
    })
