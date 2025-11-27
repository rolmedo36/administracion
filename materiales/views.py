# materiales/views.py
from django.db import models
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Material, CategoriaMaterial, Almacen, Material, StockAlmacen
from .forms import MaterialForm, CategoriaMaterialForm, AlmacenForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Sum, Case, When, DecimalField, Value
from django.db.models.functions import Coalesce

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
