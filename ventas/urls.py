from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    # Cotizaciones
    path('cotizaciones/', views.cotizacion_list, name='cotizacion_list'),
    path('cotizaciones/crear/', views.cotizacion_create, name='cotizacion_create'),
    path('cotizaciones/<int:pk>/', views.cotizacion_detail, name='cotizacion_detail'),
    path('cotizaciones/<int:pk>/enviar/', views.cotizacion_enviar, name='cotizacion_enviar'),
    path('cotizaciones/<int:pk>/aceptar/', views.cotizacion_aceptar, name='cotizacion_aceptar'),
    path('cotizaciones/<int:pk>/convertir-pedido/', views.cotizacion_convertir_pedido, name='cotizacion_convertir_pedido'),
    path('cotizaciones/<int:pk>/detalles/', views.get_detalles_cotizacion, name='get_detalles_cotizacion'),

    # PEDIDOS
    path('pedidos/', views.pedido_list, name='pedido_list'),
    path('pedidos/crear/', views.pedido_create, name='pedido_create'),
    path('pedidos/<int:pk>/', views.pedido_detail, name='pedido_detail'),
    path('pedidos/<int:pk>/confirmar/', views.pedido_confirmar, name='pedido_confirmar'),
    path('pedidos/<int:pk>/surtir/', views.pedido_surtir, name='pedido_surtir'),
    path('pedidos/cotizaciones-cliente/', views.get_cotizaciones_cliente, name='get_cotizaciones_cliente'),

    # FACTURAS
    path('facturas/', views.factura_list, name='factura_list'),
    path('facturas/crear/', views.factura_create, name='factura_create'),
    path('facturas/<int:pk>/', views.factura_detail, name='factura_detail'),
    path('facturas/<int:pk>/editar/', views.factura_update, name='factura_update'),
    path('facturas/<int:pk>/imprimir/', views.factura_print, name='factura_print'),

    # Cuentas por Cobrar
    path('cxc/', views.cxc_list, name='cxc_list'),
    path('cxc/<int:pk>/', views.cxc_detail, name='cxc_detail'),
    path('cxc/<int:cxc_id>/pagar/', views.registrar_pago_cxc, name='registrar_pago_cxc'),

    # REPORTES CXC
    path('reportes/cxc/saldos/', views.reporte_cxc_saldos, name='reporte_cxc_saldos'),
    path('reportes/cxc/aging/', views.reporte_cxc_aging, name='reporte_cxc_aging'),
    path('reportes/cxc/vencimientos/', views.reporte_cxc_vencimientos, name='reporte_cxc_vencimientos'),
    path('reportes/cxc/clientes-saldo/', views.reporte_cxc_clientes_mayor_saldo, name='reporte_cxc_clientes_mayor_saldo'),

    # Vendedores
    path('vendedores/', views.vendedor_list, name='vendedor_list'),
    path('vendedores/crear/', views.vendedor_create, name='vendedor_create'),
    path('vendedores/<int:pk>/', views.vendedor_detail, name='vendedor_detail'),
    path('vendedores/<int:pk>/editar/', views.vendedor_update, name='vendedor_update'),
    path('vendedores/<int:pk>/eliminar/', views.vendedor_delete, name='vendedor_delete'),

    # Asignación de clientes a vendedores
    path('vendedores/<int:vendedor_id>/asignar-clientes/',
         views.asignar_clientes_vendedor, name='asignar_clientes_vendedor'),
]
