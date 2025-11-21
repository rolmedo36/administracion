from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction
from .models import Banco, CuentaBancaria, MovimientoBancario
from .forms import BancoForm, CuentaBancariaForm, MovimientoBancarioForm
from django.db.models import Sum, Q
from datetime import date, timedelta
from collections import defaultdict


# --- BANCOS ---
@login_required
@permission_required('flujocaja.view_banco', raise_exception=True)
def banco_list(request):
    bancos = Banco.objects.all().order_by('nombre')
    return render(request, 'flujocaja/banco/banco_list.html', {'bancos': bancos})

@login_required
@permission_required('flujocaja.add_banco', raise_exception=True)
def banco_create(request):
    if request.method == 'POST':
        form = BancoForm(request.POST)
        if form.is_valid():
            banco = form.save(commit=False)
            banco.creado_por = request.user
            banco.save()
            messages.success(request, f"Banco {banco.nombre} creado exitosamente.")
            return redirect('flujocaja:banco_list')
    else:
        form = BancoForm()
    return render(request, 'flujocaja/banco/banco_form.html', {'form': form})

@login_required
@permission_required('flujocaja.change_banco', raise_exception=True)
def banco_update(request, pk):
    banco = get_object_or_404(Banco, pk=pk)
    if request.method == 'POST':
        form = BancoForm(request.POST, instance=banco)
        if form.is_valid():
            form.save()
            messages.success(request, f"Banco {banco.nombre} actualizado.")
            return redirect('flujocaja:banco_list')
    else:
        form = BancoForm(instance=banco)
    return render(request, 'flujocaja/banco/banco_form.html', {'form': form})

@login_required
@permission_required('flujocaja.delete_banco', raise_exception=True)
def banco_delete(request, pk):
    banco = get_object_or_404(Banco, pk=pk)
    if request.method == 'POST':
        banco.delete()
        messages.success(request, f"Banco {banco.nombre} eliminado.")
        return redirect('flujocaja:banco_list')
    return render(request, 'flujocaja/banco/banco_confirm_delete.html', {'object': banco})

# --- CUENTAS BANCARIAS ---
@login_required
@permission_required('flujocaja.view_cuentabancaria', raise_exception=True)
def cuentabancaria_list(request):
    cuentas = CuentaBancaria.objects.select_related('banco').all().order_by('banco__nombre', 'numero_cuenta')
    return render(request, 'flujocaja/cuentabancaria/cuentabancaria_list.html', {'cuentas': cuentas})

@login_required
@permission_required('flujocaja.add_cuentabancaria', raise_exception=True)
def cuentabancaria_create(request):
    if request.method == 'POST':
        form = CuentaBancariaForm(request.POST)
        if form.is_valid():
            cuenta = form.save(commit=False)
            cuenta.creado_por = request.user
            cuenta.save()
            messages.success(request, f"Cuenta {cuenta.numero_cuenta} creada exitosamente.")
            return redirect('flujocaja:cuentabancaria_list')
    else:
        form = CuentaBancariaForm()
    return render(request, 'flujocaja/cuentabancaria/cuentabancaria_form.html', {'form': form})

@login_required
@permission_required('flujocaja.change_cuentabancaria', raise_exception=True)
def cuentabancaria_update(request, pk):
    cuenta = get_object_or_404(CuentaBancaria, pk=pk)
    if request.method == 'POST':
        form = CuentaBancariaForm(request.POST, instance=cuenta)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cuenta {cuenta.numero_cuenta} actualizada.")
            return redirect('flujocaja:cuentabancaria_list')
    else:
        form = CuentaBancariaForm(instance=cuenta)
    return render(request, 'flujocaja/cuentabancaria/cuentabancaria_form.html', {'form': form})

@login_required
@permission_required('flujocaja.delete_cuentabancaria', raise_exception=True)
def cuentabancaria_delete(request, pk):
    cuenta = get_object_or_404(CuentaBancaria, pk=pk)
    if request.method == 'POST':
        cuenta.delete()
        messages.success(request, f"Cuenta {cuenta.numero_cuenta} eliminada.")
        return redirect('flujocaja:cuentabancaria_list')
    return render(request, 'flujocaja/cuentabancaria/cuentabancaria_confirm_delete.html', {'object': cuenta})

# MOVIMIENTOS CAJA

@login_required
@permission_required('flujocaja.view_movimientobancario', raise_exception=True)
def movimiento_list(request):
    movimientos = MovimientoBancario.objects.select_related(
        'cuenta_bancaria__banco', 'creado_por'
    ).all().order_by('-fecha')
    return render(request, 'flujocaja/movimiento/movimiento_list.html', {'movimientos': movimientos})

@login_required
@permission_required('flujocaja.add_movimientobancario', raise_exception=True)
def movimiento_create(request):
    if request.method == 'POST':
        form = MovimientoBancarioForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    movimiento = form.save(commit=False)
                    movimiento.creado_por = request.user
                    movimiento.save()
                    messages.success(request, f"Movimiento registrado exitosamente.")
                    return redirect('flujocaja:movimiento_list')
            except Exception as e:
                messages.error(request, f"Error al registrar el movimiento: {str(e)}")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = MovimientoBancarioForm()
    return render(request, 'flujocaja/movimiento/movimiento_form.html', {'form': form})

# REPORTES

@login_required
@permission_required('flujocaja.view_movimientobancario', raise_exception=True)
def reporte_flujo_diario(request):
    fecha = request.GET.get('fecha', date.today().isoformat())

    try:
        fecha_obj = date.fromisoformat(fecha)
    except ValueError:
        fecha_obj = date.today()

    movimientos = MovimientoBancario.objects.filter(
        fecha=fecha_obj,
        estado='registrado'
    ).select_related('cuenta_bancaria__banco').order_by('fecha', 'cuenta_bancaria')

    total_ingresos = movimientos.filter(tipo_movimiento='ingreso').aggregate(total=Sum('monto'))['total'] or 0
    total_egresos = movimientos.filter(tipo_movimiento='egreso').aggregate(total=Sum('monto'))['total'] or 0
    saldo_neto = total_ingresos - total_egresos

    return render(request, 'flujocaja/reportes/flujo_diario.html', {
        'movimientos': movimientos,
        'fecha': fecha_obj,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'saldo_neto': saldo_neto,
    })

@login_required
@permission_required('flujocaja.view_movimientobancario', raise_exception=True)
def reporte_flujo_mensual(request):
    mes = request.GET.get('mes', None)
    if not mes:
        mes = date.today().replace(day=1).strftime('%Y-%m')

    year, month = map(int, mes.split('-')[:2])

    inicio = date(year, month, 1)
    fin = (inicio.replace(month=month + 1) if month < 12 else date(year + 1, 1, 1)) - timedelta(days=1)

    movimientos = MovimientoBancario.objects.filter(
        fecha__range=[inicio, fin],
        estado='registrado'
    ).select_related('cuenta_bancaria__banco').order_by('fecha')

    total_ingresos = movimientos.filter(tipo_movimiento='ingreso').aggregate(total=Sum('monto'))['total'] or 0
    total_egresos = movimientos.filter(tipo_movimiento='egreso').aggregate(total=Sum('monto'))['total'] or 0
    saldo_neto = total_ingresos - total_egresos

    flujo_por_dia = defaultdict(lambda: {'ingresos': 0, 'egresos': 0})

    for m in movimientos:
        dia = m.fecha.day
        if m.tipo_movimiento == 'ingreso':
            flujo_por_dia[dia]['ingresos'] += float(m.monto)
        elif m.tipo_movimiento == 'egreso':
            flujo_por_dia[dia]['egresos'] += float(m.monto)

    # Calcular neto por día
    flujo_por_dia_con_neto = {}
    for dia, datos in flujo_por_dia.items():
        flujo_por_dia_con_neto[dia] = {
            'ingresos': datos['ingresos'],
            'egresos': datos['egresos'],
            'neto': datos['ingresos'] - datos['egresos']
        }

    return render(request, 'flujocaja/reportes/flujo_mensual.html', {
        'movimientos': movimientos,
        'mes': inicio.strftime('%B %Y'),
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'saldo_neto': saldo_neto,
        'flujo_por_dia': flujo_por_dia_con_neto,
    })


@login_required
@permission_required('flujocaja.view_cuentabancaria', raise_exception=True)
def reporte_saldo_cuentas(request):
    cuentas = CuentaBancaria.objects.filter(activo=True).select_related('banco')

    # ✅ Calcula el total en la vista
    total_general = sum(c.saldo_actual for c in cuentas)

    return render(request, 'flujocaja/reportes/saldo_cuentas.html', {
        'cuentas': cuentas,
        'total_general': total_general
    })

