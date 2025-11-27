from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('', views.crm_index, name='crm_index'),

    # Prospectos
    path('prospectos/', views.prospecto_list, name='prospecto_list'),
    path('prospectos/crear/', views.prospecto_create, name='prospecto_create'),
    path('prospectos/<int:pk>/', views.prospecto_detail, name='prospecto_detail'),
    path('prospectos/<int:pk>/editar/', views.prospecto_update, name='prospecto_update'),
    path('prospectos/<int:pk>/eliminar/', views.prospecto_delete, name='prospecto_delete'),

    # Oportunidades
    path('oportunidades/', views.oportunidad_list, name='oportunidad_list'),
    path('oportunidades/crear/', views.oportunidad_create, name='oportunidad_create'),
    path('oportunidades/<int:pk>/', views.oportunidad_detail, name='oportunidad_detail'),
    path('oportunidades/<int:pk>/editar/', views.oportunidad_update, name='oportunidad_update'),
    path('oportunidades/<int:pk>/eliminar/', views.oportunidad_delete, name='oportunidad_delete'),

    # Actividades
    path('actividades/', views.actividad_list, name='actividad_list'),
    path('actividades/crear/', views.actividad_create, name='actividad_create'),
    path('actividades/<int:pk>/', views.actividad_detail, name='actividad_detail'),
    path('actividades/<int:pk>/editar/', views.actividad_update, name='actividad_update'),
    path('actividades/<int:pk>/eliminar/', views.actividad_delete, name='actividad_delete'),
    path('actividades/<int:pk>/completar/', views.completar_actividad, name='completar_actividad'),

    # Plantillas de Email
    path('plantillas-email/', views.plantilla_email_list, name='plantilla_email_list'),
    path('plantillas-email/crear/', views.plantilla_email_create, name='plantilla_email_create'),
    path('plantillas-email/<int:pk>/', views.plantilla_email_detail, name='plantilla_email_detail'),
    path('plantillas-email/<int:pk>/editar/', views.plantilla_email_update, name='plantilla_email_update'),
    path('plantillas-email/<int:pk>/eliminar/', views.plantilla_email_delete, name='plantilla_email_delete'),

    # Reportes CRM
    path('reportes/pipeline/', views.reporte_pipeline_ventas, name='reporte_pipeline_ventas'),
    path('reportes/conversion/', views.reporte_tasa_conversion, name='reporte_tasa_conversion'),
    path('reportes/rendimiento/', views.reporte_rendimiento_comercial, name='reporte_rendimiento_comercial'),
    path('reportes/actividades/', views.reporte_actividades_seguimiento, name='reporte_actividades_seguimiento'),
    path('reportes/origen/', views.reporte_analisis_origen, name='reporte_analisis_origen'),

]