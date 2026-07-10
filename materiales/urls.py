from django.urls import path
from . import views

app_name = 'materiales'

urlpatterns = [
    # Materiales
    path('', views.material_list_view, name='material_list'),
    path('/', views.material_index, name='material_index'),
    path('crear/', views.material_create_view, name='material_create'),
    path('<int:pk>/editar/', views.material_update_view, name='material_update'),
    path('<int:pk>/eliminar/', views.material_delete_view, name='material_delete'),

    # Categorías
    path('categorias/', views.categoria_list_view, name='categoria_list'),
    path('categorias/crear/', views.categoria_create_view, name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.categoria_update_view, name='categoria_update'),
    path('categorias/<int:pk>/eliminar/', views.categoria_delete_view, name='categoria_delete'),

    # Almacenes
    path('almacenes/', views.almacen_list, name='almacen_list'),
    path('almacenes/crear/', views.almacen_create, name='almacen_create'),
    path('almacenes/<int:pk>/editar/', views.almacen_update, name='almacen_update'),
    path('almacenes/<int:pk>/eliminar/', views.almacen_delete, name='almacen_delete'),
    path('reportes/existencias/', views.reporte_existencias, name='reporte_existencias'),

    # Movimientos de almacen
    path('movimientos/', views.movimiento_list, name='movimiento_list'),
    path('movimientos/entrada/', views.entrada_mercancia, name='entrada_mercancia'),
    path('movimientos/salida/', views.salida_mercancia, name='salida_mercancia'),
    path('movimientos/transferencia/', views.transferencia_mercancia, name='transferencia_mercancia'),
    path('movimientos/ajuste/', views.ajuste_inventario, name='ajuste_inventario'),
    path('movimientos/<int:pk>/', views.detalle_movimiento, name='detalle_movimiento'),

    # Reportes
    path('reportes/kardex/', views.reporte_kardex, name='reporte_kardex'),
]