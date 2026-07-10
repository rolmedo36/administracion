import pandas as pd
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from datetime import datetime
from .models import Cliente
from ventas.models import Vendedor
from .forms import ClienteForm

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
@permission_required('clientes.view_cliente', raise_exception=True)
def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'clientes/cliente_detail.html', {
        'cliente': cliente,
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
