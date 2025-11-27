from django.urls import path
from . import views

app_name = 'flujocaja'

urlpatterns = [
    path('', views.flujocaja_index, name='flujocaja_index'),

    # Bancos
    path('bancos/', views.banco_list, name='banco_list'),
    path('bancos/crear/', views.banco_create, name='banco_create'),
    path('bancos/<int:pk>/editar/', views.banco_update, name='banco_update'),
    path('bancos/<int:pk>/eliminar/', views.banco_delete, name='banco_delete'),

    # Cuentas Bancarias
    path('cuentas/', views.cuentabancaria_list, name='cuentabancaria_list'),
    path('cuentas/crear/', views.cuentabancaria_create, name='cuentabancaria_create'),
    path('cuentas/<int:pk>/editar/', views.cuentabancaria_update, name='cuentabancaria_update'),
    path('cuentas/<int:pk>/eliminar/', views.cuentabancaria_delete, name='cuentabancaria_delete'),

    # Movimientos
    path('movimientos/', views.movimiento_list, name='movimiento_list'),
    path('movimientos/crear/', views.movimiento_create, name='movimiento_create'),

    # Reportes
    path('reportes/flujo/diario/', views.reporte_flujo_diario, name='reporte_flujo_diario'),
    path('reportes/flujo/mensual/', views.reporte_flujo_mensual, name='reporte_flujo_mensual'),
    path('reportes/saldo/cuentas/', views.reporte_saldo_cuentas, name='reporte_saldo_cuentas'),
    
]