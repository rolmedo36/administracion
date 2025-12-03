from django.core.paginator import Paginator
from django.db import models
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db import transaction
from .models import Material, CategoriaMaterial, Almacen, Material, StockAlmacen, MovimientoAlmacen, DetalleMovimientoAlmacen
from .forms import MaterialForm, CategoriaMaterialForm, AlmacenForm, MovimientoAlmacenForm, DetalleMovimientoFormSet, EntradaMovimientoForm, SalidaMovimientoForm, TransferenciaMovimientoForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Sum, Case, When, DecimalField, Value, F
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.db.models import Value, CharField, OuterRef, Subquery


@login_required
@permission_required('compras.view_proveedor', raise_exception=True)
def material_index(request):
    return render(request, 'materiales/material_index.html', {'titulo': "Materiales"})

class MaterialListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Material
    template_name = 'materiales/material_list.html'
    context_object_name = 'materiales'
    permission_required = 'materiales.view_material'
    paginate_by = 8

    def get_queryset(self):
        queryset = Material.objects.all()
        categoria = self.request.GET.get('categoria')
        activo = self.request.GET.get('activo')
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        if activo is not None:
            queryset = queryset.filter(activo=(activo == '1'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaMaterial.objects.all()
        return context

class MaterialCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Material
    form_class = MaterialForm
    template_name = 'materiales/material_form.html'
    success_url = reverse_lazy('materiales:material_list')
    permission_required = 'materiales.add_material'

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        return super().form_valid(form)

class MaterialUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Material
    form_class = MaterialForm
    template_name = 'materiales/material_form.html'
    success_url = reverse_lazy('materiales:material_list')
    permission_required = 'materiales.change_material'

class MaterialDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Material
    template_name = 'materiales/material_confirm_delete.html'
    success_url = reverse_lazy('materiales:material_list')
    permission_required = 'materiales.delete_material'

# materiales/views.py (agrega al final)


class CategoriaMaterialListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = CategoriaMaterial
    template_name = 'materiales/categoria_list.html'
    context_object_name = 'categorias'
    permission_required = 'materiales.view_categoriamaterial'
    ordering = ['nombre']

class CategoriaMaterialCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = CategoriaMaterial
    form_class = CategoriaMaterialForm
    template_name = 'materiales/categoria_form.html'
    success_url = reverse_lazy('materiales:categoria_list')
    permission_required = 'materiales.add_categoriamaterial'

class CategoriaMaterialUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = CategoriaMaterial
    form_class = CategoriaMaterialForm
    template_name = 'materiales/categoria_form.html'
    success_url = reverse_lazy('materiales:categoria_list')
    permission_required = 'materiales.change_categoriamaterial'

class CategoriaMaterialDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = CategoriaMaterial
    template_name = 'materiales/categoria_confirm_delete.html'
    success_url = reverse_lazy('materiales:categoria_list')
    permission_required = 'materiales.delete_categoriamaterial'

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except models.ProtectedError:
            messages.error(request, "No se puede eliminar esta categoría porque está asociada a uno o más materiales.")
            return redirect(self.success_url)

# ALMACENES

@login_required
@permission_required('materiales.view_almacen', raise_exception=True)
def almacen_list(request):
    almacenes = Almacen.objects.all().order_by('nombre')
    return render(request, 'materiales/almacen_list.html', {'almacenes': almacenes})

@login_required
@permission_required('materiales.add_almacen', raise_exception=True)
def almacen_create(request):
    if request.method == 'POST':
        form = AlmacenForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Almacén creado exitosamente.")
            return redirect('materiales:almacen_list')
    else:
        form = AlmacenForm()
    return render(request, 'materiales/almacen_form.html', {'form': form})

@login_required
@permission_required('materiales.change_almacen', raise_exception=True)
def almacen_update(request, pk):
    almacen = get_object_or_404(Almacen, pk=pk)
    if request.method == 'POST':
        form = AlmacenForm(request.POST, instance=almacen)
        if form.is_valid():
            form.save()
            messages.success(request, "Almacén actualizado.")
            return redirect('materiales:almacen_list')
    else:
        form = AlmacenForm(instance=almacen)
    return render(request, 'materiales/almacen_form.html', {'form': form})

@login_required
@permission_required('materiales.delete_almacen', raise_exception=True)
def almacen_delete(request, pk):
    almacen = get_object_or_404(Almacen, pk=pk)
    if request.method == 'POST':
        almacen.delete()
        messages.success(request, "Almacén eliminado.")
        return redirect('materiales:almacen_list')
    return render(request, 'materiales/almacen_confirm_delete.html', {'object': almacen})

# REPORTE
@login_required
@permission_required('materiales.view_stockalmacen', raise_exception=True)
def reporte_existencias(request):
    almacenes = Almacen.objects.filter(activo=True).order_by('nombre')

    almacen_id = request.GET.get('almacen')
    material_query = request.GET.get('material')

    # Empezamos con todos los stocks de materiales inventariables
    stocks = StockAlmacen.objects.filter(
        material__activo=True,
        material__es_inventariable=True
    ).select_related('material', 'almacen')

    # Filtro por almacén
    if almacen_id:
        stocks = stocks.filter(almacen_id=almacen_id)

    # Filtro por material
    if material_query:
        stocks = stocks.filter(
            Q(material__codigo__icontains=material_query) |
            Q(material__nombre__icontains=material_query)
        )

    # Convertir a lista de resultados
    resultados = []
    for stock in stocks:
        resultados.append({
            'material': stock.material,
            'almacen': stock.almacen,
            'cantidad': stock.cantidad
        })

    # Si se filtró por un almacén, agregamos materiales inventariables faltantes con cantidad 0
    if almacen_id:
        almacen = Almacen.objects.get(id=almacen_id)
        materiales_con_stock = {item['material'].id for item in resultados}
        todos_materiales = Material.objects.filter(
            activo=True,
            es_inventariable=True
        )
        if material_query:
            todos_materiales = todos_materiales.filter(
                Q(codigo__icontains=material_query) |
                Q(nombre__icontains=material_query)
            )

        for material in todos_materiales:
            if material.id not in materiales_con_stock:
                resultados.append({
                    'material': material,
                    'almacen': almacen,
                    'cantidad': 0
                })

    # Ordenar
    resultados.sort(key=lambda x: (x['material'].nombre, x['almacen'].nombre))

    # Calcular total (solo si un almacén)
    total_cantidad = None
    if almacen_id:
        total_cantidad = sum(item['cantidad'] for item in resultados)

    return render(request, 'materiales/reporte_existencias.html', {
        'resultados': resultados,
        'almacenes': almacenes,
        'almacen_seleccionado': almacen_id,
        'material_query': material_query,
        'total_cantidad': total_cantidad,
    })

# MOVIMIENTOS DE ALMACEN

@login_required
@permission_required('materiales.view_movimientoalmacen', raise_exception=True)
def movimiento_list(request):
    """Lista de movimientos de almacén con filtros."""
    movimientos = MovimientoAlmacen.objects.select_related(
        'almacen_origen', 'almacen_destino', 'creado_por'
    ).prefetch_related('detalles').all()

    # Filtros
    search = request.GET.get('search')
    tipo = request.GET.get('tipo')
    almacen = request.GET.get('almacen')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if search:
        movimientos = movimientos.filter(
            Q(documento_referencia__icontains=search) |
            Q(notas__icontains=search)
        )
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)
    if almacen:
        movimientos = movimientos.filter(
            Q(almacen_origen_id=almacen) | Q(almacen_destino_id=almacen)
        )
    if fecha_desde:
        movimientos = movimientos.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        movimientos = movimientos.filter(fecha__lte=fecha_hasta)

    movimientos = movimientos.order_by('-fecha')

    # Paginación
    paginator = Paginator(movimientos, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Opciones para filtros
    tipos = MovimientoAlmacen._meta.get_field('tipo').choices
    almacenes = Almacen.objects.filter(activo=True)

    return render(request, 'materiales/almacen/movimiento_list.html', {
        'movimientos': page_obj,
        'tipos': tipos,
        'almacenes': almacenes,
        'search_query': search,
        'tipo_filtro': tipo,
        'almacen_filtro': almacen,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    })

@login_required
@permission_required('materiales.add_movimientoalmacen', raise_exception=True)
def ajuste_inventario(request):
    """Crear ajuste de inventario (positivo o negativo)."""
    if request.method == 'POST':
        tipo_ajuste = request.POST.get('tipo_ajuste', 'positivo')
        form = MovimientoAlmacenForm(request.POST, tipo='ajuste')
        formset = DetalleMovimientoFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    movimiento = form.save(commit=False)
                    movimiento.tipo = 'entrada_ajuste_positivo' if tipo_ajuste == 'positivo' else 'salida_ajuste_negativo'
                    movimiento.creado_por = request.user

                    if not movimiento.almacen_origen:
                        raise ValueError("Almacén es requerido para ajustes")

                    movimiento.almacen_destino = movimiento.almacen_origen
                    movimiento.save()

                    detalles = formset.save(commit=False)
                    for detalle in detalles:
                        detalle.movimiento = movimiento
                        detalle.save()

                    movimiento.confirmar(request.user)
                    messages.success(request, f"Ajuste {tipo_ajuste} registrado exitosamente.")
                    return redirect('materiales:detalle_movimiento', pk=movimiento.pk)
            except Exception as e:
                messages.error(request, f"Error al registrar el ajuste: {str(e)}")
    else:
        form = MovimientoAlmacenForm(tipo='ajuste')
        formset = DetalleMovimientoFormSet()

    almacenes = Almacen.objects.filter(activo=True)
    materiales = Material.objects.filter(activo=True, es_inventariable=True)

    return render(request, 'materiales/almacen/ajuste/ajuste_form.html', {
        'form': form,
        'formset': formset,
        'almacenes': almacenes,
        'materiales': materiales,
    })

@login_required
@permission_required('materiales.view_movimientoalmacen', raise_exception=True)
def detalle_movimiento(request, pk):
    """Ver detalle de un movimiento de almacén."""
    movimiento = get_object_or_404(MovimientoAlmacen, pk=pk)
    return render(request, 'materiales/almacen/movimiento_detail.html', {
        'movimiento': movimiento
    })

@login_required
@permission_required('materiales.add_movimientoalmacen', raise_exception=True)
def entrada_mercancia(request):
    """Crear entrada de mercancía por orden de compra."""
    if request.method == 'POST':
        form = EntradaMovimientoForm(request.POST)
        formset = DetalleMovimientoFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    movimiento = form.save(commit=False)
                    movimiento.tipo = 'entrada_compra'
                    movimiento.creado_por = request.user
                    movimiento.save()

                    detalles = formset.save(commit=False)
                    for detalle in detalles:
                        detalle.movimiento = movimiento
                        detalle.save()

                    movimiento.confirmar(request.user)
                    messages.success(request, "Entrada de mercancía registrada exitosamente.")
                    return redirect('materiales:detalle_movimiento', pk=movimiento.pk)
            except Exception as e:
                messages.error(request, f"Error al registrar la entrada: {str(e)}")
    else:
        form = EntradaMovimientoForm()
        formset = DetalleMovimientoFormSet()

    almacenes = Almacen.objects.filter(activo=True)
    materiales = Material.objects.filter(activo=True, es_inventariable=True)

    return render(request, 'materiales/almacen/entrada/entrada_form.html', {
        'form': form,
        'formset': formset,
        'almacenes': almacenes,
        'materiales': materiales,
    })


@login_required
@permission_required('materiales.add_movimientoalmacen', raise_exception=True)
def salida_mercancia(request):
    """Crear salida de mercancía por venta o devolución."""
    if request.method == 'POST':
        form = SalidaMovimientoForm(request.POST)
        formset = DetalleMovimientoFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    movimiento = form.save(commit=False)
                    movimiento.tipo = 'salida_venta'
                    movimiento.creado_por = request.user
                    movimiento.save()

                    detalles = formset.save(commit=False)
                    for detalle in detalles:
                        detalle.movimiento = movimiento
                        detalle.save()

                    movimiento.confirmar(request.user)
                    messages.success(request, "Salida de mercancía registrada exitosamente.")
                    return redirect('materiales:detalle_movimiento', pk=movimiento.pk)
            except Exception as e:
                messages.error(request, f"Error al registrar la salida: {str(e)}")
    else:
        form = SalidaMovimientoForm()
        formset = DetalleMovimientoFormSet()

    almacenes = Almacen.objects.filter(activo=True)
    materiales = Material.objects.filter(activo=True, es_inventariable=True)

    return render(request, 'materiales/almacen/salida/salida_form.html', {
        'form': form,
        'formset': formset,
        'almacenes': almacenes,
        'materiales': materiales,
    })


@login_required
@permission_required('materiales.add_movimientoalmacen', raise_exception=True)
def transferencia_mercancia(request):
    """Crear transferencia entre almacenes."""
    if request.method == 'POST':
        form = TransferenciaMovimientoForm(request.POST)
        formset = DetalleMovimientoFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    movimiento = form.save(commit=False)
                    movimiento.tipo = 'transferencia'
                    movimiento.creado_por = request.user
                    movimiento.save()

                    detalles = formset.save(commit=False)
                    for detalle in detalles:
                        detalle.movimiento = movimiento
                        detalle.save()

                    movimiento.confirmar(request.user)
                    messages.success(request, "Transferencia registrada exitosamente.")
                    return redirect('materiales:detalle_movimiento', pk=movimiento.pk)
            except Exception as e:
                messages.error(request, f"Error al registrar la transferencia: {str(e)}")
    else:
        form = TransferenciaMovimientoForm()
        formset = DetalleMovimientoFormSet()

    almacenes = Almacen.objects.filter(activo=True)
    materiales = Material.objects.filter(activo=True, es_inventariable=True)

    return render(request, 'materiales/almacen/transferencia/transferencia_form.html', {
        'form': form,
        'formset': formset,
        'almacenes': almacenes,
        'materiales': materiales,
    })

# Reportes

@login_required
@permission_required('materiales.view_stockalmacen', raise_exception=True)
def reporte_kardex(request):
    """Reporte de Kardex por material y almacén."""
    movimientos = []
    material_seleccionado = None
    almacen_seleccionado = None
    saldo_inicial = Decimal('0')
    saldo_final = Decimal('0')

    material_id = request.GET.get('material')
    almacen_id = request.GET.get('almacen')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if material_id and almacen_id:
        try:
            # Obtener el material y almacén
            material_seleccionado = get_object_or_404(Material, id=material_id)
            almacen_seleccionado = get_object_or_404(Almacen, id=almacen_id)

            # Obtener todos los movimientos relacionados con este material y almacén
            entradas = []
            salidas = []

            # Buscar entradas (material entra al almacén)
            movimientos_entrada = MovimientoAlmacen.objects.filter(
                Q(almacen_destino=almacen_seleccionado) & Q(tipo__startswith='entrada') |
                Q(almacen_destino=almacen_seleccionado) & Q(tipo='transferencia'),
                detalles__material=material_seleccionado,
                estado='confirmado'
            ).prefetch_related('detalles', 'creado_por').order_by('fecha')

            for mov in movimientos_entrada:
                for detalle in mov.detalles.all():
                    if detalle.material == material_seleccionado:
                        entradas.append({
                            'fecha': mov.fecha,
                            'tipo': mov.get_tipo_display(),
                            'tipo_movimiento': 'entrada',
                            'documento_referencia': mov.documento_referencia,
                            'cantidad': detalle.cantidad,
                            'notas': mov.notas,
                            'usuario': mov.creado_por.username if mov.creado_por else 'Sistema'
                        })

            # Buscar salidas (material sale del almacén)
            movimientos_salida = MovimientoAlmacen.objects.filter(
                Q(almacen_origen=almacen_seleccionado) & Q(tipo__startswith='salida') |
                Q(almacen_origen=almacen_seleccionado) & Q(tipo='transferencia'),
                detalles__material=material_seleccionado,
                estado='confirmado'
            ).prefetch_related('detalles', 'creado_por').order_by('fecha')

            for mov in movimientos_salida:
                for detalle in mov.detalles.all():
                    if detalle.material == material_seleccionado:
                        salidas.append({
                            'fecha': mov.fecha,
                            'tipo': mov.get_tipo_display(),
                            'tipo_movimiento': 'salida',
                            'documento_referencia': mov.documento_referencia,
                            'cantidad': detalle.cantidad,
                            'notas': mov.notas,
                            'usuario': mov.creado_por.username if mov.creado_por else 'Sistema'
                        })

            # Combinar y ordenar todos los movimientos
            todos_movimientos = entradas + salidas
            todos_movimientos.sort(key=lambda x: x['fecha'])

            # Calcular saldo acumulado
            saldo = Decimal('0')
            for movimiento in todos_movimientos:
                if movimiento['tipo_movimiento'] == 'entrada':
                    saldo += movimiento['cantidad']
                else:
                    saldo -= movimiento['cantidad']
                movimiento['saldo'] = saldo

            movimientos = todos_movimientos
            saldo_final = saldo

        except Exception as e:
            messages.error(request, f"Error al generar el kardex: {str(e)}")

    materiales = Material.objects.filter(activo=True, es_inventariable=True)
    almacenes = Almacen.objects.filter(activo=True)

    return render(request, 'materiales/reportes/kardex.html', {
        'movimientos': movimientos,
        'materiales': materiales,
        'almacenes': almacenes,
        'material_seleccionado': material_seleccionado,
        'almacen_seleccionado': almacen_seleccionado,
        'saldo_inicial': saldo_inicial,
        'saldo_final': saldo_final,
    })

