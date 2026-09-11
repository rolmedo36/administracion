from django.contrib import admin
from .models import Mecanico, Vehiculo, OrdenServicio, ItemOrdenServicio, PagoOrdenServicio, VehiculoInventario


@admin.register(Mecanico)
class MecanicoAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'especialidad', 'telefono', 'activo')
    list_filter = ('activo', 'especialidad')
    search_fields = ('nombre', 'apellido', 'telefono', 'email')
    list_editable = ('activo',)


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('marca', 'modelo', 'año', 'placa', 'tipo', 'cliente')
    list_filter = ('tipo', 'marca')
    search_fields = ('placa', 'vin', 'marca', 'modelo', 'cliente__nombre')
    raw_id_fields = ('cliente',)


class ItemOrdenServicioInline(admin.TabularInline):
    model = ItemOrdenServicio
    extra = 1
    fields = ('tipo', 'descripcion', 'cantidad', 'precio_unitario', 'subtotal')
    readonly_fields = ('subtotal',)


@admin.register(OrdenServicio)
class OrdenServicioAdmin(admin.ModelAdmin):
    list_display = ('numero_os', 'cliente', 'vehiculo', 'tipo_servicio',
                    'estado', 'mecanico_responsable', 'fecha_entrada', 'total')
    list_filter = ('estado', 'tipo_servicio', 'mecanico_responsable')
    search_fields = ('numero_os', 'cliente__nombre', 'vehiculo__placa',
                     'vehiculo__marca', 'vehiculo__modelo')
    date_hierarchy = 'fecha_entrada'
    raw_id_fields = ('cliente', 'vehiculo', 'mecanico_responsable')
    readonly_fields = ('numero_os', 'subtotal_refacciones', 'subtotal_mano_obra',
                       'total', 'fecha_creacion', 'fecha_actualizacion')
    inlines = [ItemOrdenServicioInline]

    fieldsets = (
        ('Información General', {
            'fields': ('numero_os', 'cliente', 'vehiculo', 'mecanico_responsable',
                       'tipo_servicio', 'estado')
        }),
        ('Entrada del Vehículo', {
            'fields': ('fecha_entrada', 'fecha_salida', 'kilometraje_entrada')
        }),
        ('Diagnóstico', {
            'fields': ('sintoma_cliente', 'diagnostico_mecanico',
                       'costo_diagnostico', 'diagnostico_aplicado'),
            'classes': ('collapse',)
        }),
        ('Trabajo Técnico', {
            'fields': ('notas_tecnicas',),
            'classes': ('collapse',)
        }),
        ('Cotización y Pago', {
            'fields': ('subtotal_refacciones', 'subtotal_mano_obra',
                       'descuento', 'total', 'metodo_pago', 'garantia_dias')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

@admin.register(VehiculoInventario)
class VehiculoInventarioAdmin(admin.ModelAdmin):
   list_display = ('marca', 'modelo', 'año', 'vin', 'estado', 'precio_venta', 'fecha_ingreso')
   list_filter = ('estado', 'marca', 'año')
   search_fields = ('vin', 'marca', 'modelo', 'placa')
   readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'costo_reparacion_interna')
   list_per_page = 20