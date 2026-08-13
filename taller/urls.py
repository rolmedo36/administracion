from django.urls import path
from . import views

app_name = 'taller'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_taller, name='dashboard_taller'),

    # Órdenes de Servicio
    path('ordenes/', views.lista_ordenes, name='lista_ordenes'),
    path('ordenes/nueva/', views.crear_orden, name='crear_orden'),
    path('ordenes/<int:pk>/', views.detalle_orden, name='detalle_orden'),
    path('ordenes/<int:pk>/editar/', views.editar_orden, name='editar_orden'),
    path('ordenes/<int:pk>/estado/<str:nuevo_estado>/', views.cambiar_estado_orden, name='cambiar_estado_orden'),

    # Ítems de Orden de Servicio
    path('ordenes/<int:pk>/agregar-item/', views.agregar_item, name='agregar_item'),
    path('items/<int:pk_item>/eliminar/', views.eliminar_item, name='eliminar_item'),

    # CRUD de Mecánicos
    path('mecanicos/', views.lista_mecanicos, name='lista_mecanicos'),
    path('mecanicos/nuevo/', views.crear_mecanico, name='crear_mecanico'),
    path('mecanicos/<int:pk>/editar/', views.editar_mecanico, name='editar_mecanico'),

    # CRUD de Vehículos
    path('vehiculos/', views.lista_vehiculos, name='lista_vehiculos'),
    path('vehiculos/nuevo/', views.crear_vehiculo, name='crear_vehiculo'),
    path('vehiculos/<int:pk>/editar/', views.editar_vehiculo, name='editar_vehiculo'),

    # Pagos
    path('ordenes/<int:pk>/registrar-pago/', views.registrar_pago, name='registrar_pago'),

    # Reportes
    path('reportes/servicios/', views.reporte_servicios, name='reporte_servicios'),
    path('reportes/servicios/excel/', views.reporte_servicios_excel, name='reporte_servicios_excel'),
    path('reportes/ejecutivo/', views.reporte_ejecutivo, name='reporte_ejecutivo'),
    path('reportes/clientes-inactivos/', views.reporte_clientes_inactivos, name='reporte_clientes_inactivos'),

    # Impresión
    path('ordenes/<int:pk>/imprimir/', views.imprimir_orden, name='imprimir_orden'),

    # Buscador
    path('ajax/buscar-productos/', views.buscar_productos, name='buscar_productos'),
    path('ajax/vehiculos-por-cliente/<int:cliente_id>/', views.vehiculos_por_cliente, name='vehiculos_por_cliente'),

]