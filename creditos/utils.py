from datetime import timedelta
from decimal import Decimal, getcontext

getcontext().prec = 28


def add_months(source_date, months):
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day,
              [31, 29 if year % 4 == 0 and not year % 100 == 0 or year % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30,
               31, 30, 31][month - 1])
    return source_date.replace(year=year, month=month, day=day)


def generar_amortizacion_frances(credito):
    amortizaciones = []
    saldo = credito.monto_original
    tasa = credito.tasa_interes / Decimal('100')  # Convertir % a decimal
    n = credito.num_cuotas

    if tasa == 0:
        cuota_fija = saldo / n
    else:
        cuota_fija = saldo * (tasa / (1 - (1 + tasa) ** (-n)))

    fecha_pago = credito.fecha_inicio_pagos

    for i in range(1, n + 1):
        interes = saldo * tasa
        capital = cuota_fija - interes
        if capital > saldo:
            capital = saldo
            cuota_fija = capital + interes

        amortizaciones.append({
            'numero_cuota': i,
            'fecha_vencimiento': fecha_pago,
            'capital': capital,
            'interes': interes,
            'monto_total': cuota_fija,
        })

        saldo -= capital
        if credito.frecuencia_pagos == 'mensual':
            fecha_pago = add_months(fecha_pago, 1)
        elif credito.frecuencia_pagos == 'quincenal':
            fecha_pago += timedelta(days=15)
        else:  # semanal
            fecha_pago += timedelta(weeks=1)

    return amortizaciones


def generar_amortizacion_americano(credito):
    amortizaciones = []
    saldo = credito.monto_original
    tasa = credito.tasa_interes / Decimal('100')
    fecha_pago = credito.fecha_inicio_pagos

    for i in range(1, credito.num_cuotas + 1):
        interes = saldo * tasa

        if i == credito.num_cuotas:  # Última cuota: capital + interés
            capital = saldo
            monto_total = capital + interes
        else:  # Cuotas intermedias: solo interés
            capital = Decimal('0')
            monto_total = interes

        amortizaciones.append({
            'numero_cuota': i,
            'fecha_vencimiento': fecha_pago,
            'capital': capital,
            'interes': interes,
            'monto_total': monto_total,
        })

        if credito.frecuencia_pagos == 'mensual':
            fecha_pago = add_months(fecha_pago, 1)
        elif credito.frecuencia_pagos == 'quincenal':
            fecha_pago += timedelta(days=15)
        else:
            fecha_pago += timedelta(weeks=1)

    return amortizaciones