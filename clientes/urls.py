from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.cliente_list, name='cliente_list'),
    path('/', views.cliente_index, name='cliente_index'),
    path('crear/', views.cliente_create, name='cliente_create'),
    path('<int:pk>/editar/', views.cliente_update, name='cliente_update'),
    path('<int:pk>/', views.cliente_detail, name='cliente_detail'),

    # Actividad cliente
    path('<int:pk>/actividad/crear/', views.crear_actividad_cliente, name='crear_actividad'),
    path('<int:pk>/', views.cliente_detail, name='cliente_detail'),
    path('actividad/<int:actividad_id>/completar/', views.completar_tarea, name='completar_tarea'),
    path('actividad/<int:actividad_id>/cerrar-reunion/', views.cerrar_reunion, name='cerrar_reunion'),
    path('<int:pk>/', views.cliente_detail, name='cliente_detail'),

    # Subir documentos
    path('<int:pk>/documento/subir/', views.subir_documento_cliente, name='subir_documento'),
]