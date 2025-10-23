from django.urls import path
from . import views

app_name = 'creditos'

urlpatterns = [
    path('', views.credito_list, name='credito_list'),
    path('/', views.credito_index, name='credito_index'),
    path('crear/', views.credito_create, name='credito_create'),
    path('<int:pk>/', views.credito_detail, name='credito_detail'),
    path('amortizacion/<int:amortizacion_id>/pagar/', views.registrar_pago_credito, name='registrar_pago_credito'),
    path('reportes/vencimientos/', views.reporte_vencimientos, name='reporte_vencimientos'),
    path('pago/<int:pago_id>/', views.detalle_pago, name='detalle_pago'),
]