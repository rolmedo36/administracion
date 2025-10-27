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
]