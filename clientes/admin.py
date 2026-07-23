from django.contrib import admin
from .models import Cliente, ActividadCliente  # Asegúrate de importar el nuevo modelo


@admin.register(ActividadCliente)
class ActividadClienteAdmin(admin.ModelAdmin):
    # Campos que se mostrarán en la lista del admin
    list_display = ('titulo', 'cliente', 'tipo', 'estado', 'fecha_programada', 'es_privado', 'creado_por')

    # Filtros laterales para buscar rápido
    list_filter = ('tipo', 'estado', 'es_privado', 'fecha_creacion')

    # Campos por los que podrás buscar en la barra de búsqueda
    search_fields = ('titulo', 'descripcion', 'cliente__nombre')
    # Nota: Si el campo de nombre de tu cliente no se llama 'nombre', ajústalo (ej. 'cliente__razon_social')

    # Orden por defecto
    ordering = ('-fecha_creacion',)

    # Campos de solo lectura (auditoría)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')