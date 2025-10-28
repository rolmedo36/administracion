from django.urls import path
from . import views

app_name = 'compras'

urlpatterns = [
    # Proveedores
    path('proveedores/', views.proveedor_list, name='proveedor_list'),
    path('proveedores/crear/', views.proveedor_create, name='proveedor_create'),
    path('proveedores/<int:pk>/editar/', views.proveedor_update, name='proveedor_update'),
    path('proveedores/<int:pk>/eliminar/', views.proveedor_delete, name='proveedor_delete'),

    # Órdenes de Compra
    path('/', views.compras_index, name='compras_index'),
    path('ordenes/', views.ordencompra_list, name='ordencompra_list'),
    path('ordenes/crear/', views.ordencompra_create, name='ordencompra_create'),
    path('ordenes/<int:pk>/', views.ordencompra_detail, name='ordencompra_detail'),
    path('ordenes/<int:pk>/editar/', views.ordencompra_update, name='ordencompra_update'),
    path('ordenes/<int:pk>/eliminar/', views.ordencompra_delete, name='ordencompra_delete'),
    path('ordenes/<int:pk>/recepcionar/', views.recepcion_orden, name='recepcion_orden'),
    path('ordenes/por-recibir/', views.ordenes_por_recibir, name='ordenes_por_recibir'),
    # CXP
    path('cxp/<int:cxp_id>/', views.detalle_cxp, name='detalle_cxp'),
    path('cxp/<int:cxp_id>/pagar/', views.registrar_pago_cxp, name='registrar_pago_cxp'),
    path('reportes/cxp/', views.reporte_cxp, name='reporte_cxp'),
]