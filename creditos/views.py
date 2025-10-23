# creditos/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction
from .models import CreditoProveedor, AmortizacionCredito, PagoCredito
from .forms import CreditoProveedorForm, PagoCreditoForm
from datetime import date, timedelta
from django.db.models import Sum


@login_required
@permission_required('creditos.view_creditoproveedor', raise_exception=True)
def credito_index(request):
    return render(request, 'creditos/credito_index.html', {'titulo': 'Créditos'})

@login_required
@permission_required('creditos.view_creditoproveedor', raise_exception=True)
def credito_list(request):
    creditos = CreditoProveedor.objects.select_related('proveedor').all()
    return render(request, 'creditos/credito_list.html', {'creditos': creditos})


@login_required
@permission_required('creditos.add_creditoproveedor', raise_exception=True)
def credito_create(request):
    if request.method == 'POST':
        form = CreditoProveedorForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    credito = form.save(commit=False)
                    credito.saldo_actual = credito.monto_original
                    credito.creado_por = request.user
                    credito.save()

                    # Generar amortizaciones
                    amortizaciones = credito.calcular_amortizaciones()
                    for amort in amortizaciones:
                        AmortizacionCredito.objects.create(
                            credito=credito,
                            numero_cuota=amort['numero_cuota'],
                            fecha_vencimiento=amort['fecha_vencimiento'],
                            capital=amort['capital'],
                            interes=amort['interes'],
                            monto_total=amort['monto_total']
                        )

                    messages.success(request, f"Crédito {credito.referencia} creado exitosamente.")
                    return redirect('creditos:credito_detail', pk=credito.pk)
            except Exception as e:
                messages.error(request, f"Error al crear el crédito: {str(e)}")
    else:
        form = CreditoProveedorForm()

    return render(request, 'creditos/credito_form.html', {'form': form})


@login_required
@permission_required('creditos.view_creditoproveedor', raise_exception=True)
def credito_detail(request, pk):
    credito = get_object_or_404(CreditoProveedor, pk=pk)
    return render(request, 'creditos/credito_detail.html', {'credito': credito})


@login_required
@permission_required('creditos.add_pagocredito', raise_exception=True)
def registrar_pago_credito(request, amortizacion_id):
    amortizacion = get_object_or_404(AmortizacionCredito, id=amortizacion_id)

    if amortizacion.estado == 'pagado':
        messages.error(request, "Esta cuota ya ha sido pagada.")
        return redirect('creditos:credito_detail', pk=amortizacion.credito.pk)

    if request.method == 'POST':
        form = PagoCreditoForm(request.POST, amortizacion=amortizacion)
        if form.is_valid():
            try:
                pago = form.save(commit=False)
                pago.amortizacion = amortizacion
                pago.creado_por = request.user
                pago.save()
                messages.success(request, f"Pago de ${pago.monto_pagado} registrado exitosamente.")
                return redirect('creditos:credito_detail', pk=amortizacion.credito.pk)
            except Exception as e:
                messages.error(request, f"Error al registrar el pago: {str(e)}")
    else:
        form = PagoCreditoForm(amortizacion=amortizacion)

    return render(request, 'creditos/pago_credito_form.html', {
        'form': form,
        'amortizacion': amortizacion
    })


@login_required
@permission_required('creditos.view_creditoproveedor', raise_exception=True)
def reporte_vencimientos(request):
    fecha_hasta = request.GET.get('fecha_hasta')
    if not fecha_hasta:
        fecha_hasta = (date.today() + timedelta(days=30)).isoformat()

    vencimientos = AmortizacionCredito.objects.filter(
        estado='pendiente',
        fecha_vencimiento__lte=fecha_hasta
    ).select_related('credito__proveedor').order_by('fecha_vencimiento')

    # Calcular total
    total_monto = vencimientos.aggregate(total=Sum('monto_total'))['total'] or 0

    return render(request, 'creditos/reporte_vencimientos.html', {
        'vencimientos': vencimientos,
        'fecha_hasta': fecha_hasta,
        'total_monto': total_monto,
        'today': date.today(),  # Para resaltar vencidos
    })

@login_required
@permission_required('creditos.view_pagocredito', raise_exception=True)
def detalle_pago(request, pago_id):
    pago = get_object_or_404(PagoCredito, id=pago_id)
    return render(request, 'creditos/pago_credito_detail.html', {'pago': pago})