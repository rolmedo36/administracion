from django.db import models
from django.contrib.auth.models import User


class Mecanico(models.Model):
    """Modelo para gestionar los mecánicos del taller"""

    # Datos básicos
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Relación opcional con usuario del sistema (si el mecánico también usa el sistema)
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='mecanico')

    # Estado y especialidad
    activo = models.BooleanField(default=True)
    especialidad = models.CharField(max_length=100, blank=True, null=True,
                                    help_text="Ej: Mecánica general, Electricidad, Pintura")

    # Notas
    notas = models.TextField(blank=True, null=True)

    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mecánico"
        verbose_name_plural = "Mecánicos"
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"


class Vehiculo(models.Model):
    """Modelo genérico para gestionar vehículos (motos, autos, camionetas)"""

    # Tipos de vehículo
    TIPO_MOTO = 'MOTO'
    TIPO_AUTO = 'AUTO'
    TIPO_CAMIONETA = 'CAMIONETA'

    TIPOS_VEHICULO = [
        (TIPO_MOTO, '🏍️ Motocicleta'),
        (TIPO_AUTO, '🚗 Automóvil'),
        (TIPO_CAMIONETA, '🛻 Camioneta'),
    ]

    # Relación con cliente existente
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE, related_name='vehiculos')

    # Información básica
    tipo = models.CharField(max_length=20, choices=TIPOS_VEHICULO)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    año = models.PositiveIntegerField()
    placa = models.CharField(max_length=20, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)

    # Información específica (opcional según tipo)
    vin = models.CharField(max_length=17, blank=True, null=True,
                           help_text="Número de identificación vehicular (17 caracteres)")
    cilindrada = models.PositiveIntegerField(blank=True, null=True,
                                             help_text="En CC, solo para motos")

    # Estado actual
    kilometraje_actual = models.PositiveIntegerField(blank=True, null=True)

    # Notas generales del vehículo
    notas = models.TextField(blank=True, null=True,
                             help_text="Observaciones generales del vehículo")

    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.marca} {self.modelo} {self.año} - {self.placa or 'Sin placa'}"

    @property
    def descripcion_completa(self):
        return f"{self.get_tipo_display()} {self.marca} {self.modelo} {self.año}"

class OrdenServicio(models.Model):
    """Modelo principal para gestionar las órdenes de servicio del taller"""

    # Estados de la orden
    ESTADO_NUEVA = 'NUEVA'
    ESTADO_EN_DIAGNOSTICO = 'EN_DIAGNOSTICO'
    ESTADO_COTIZADA = 'COTIZADA'
    ESTADO_APROBADA = 'APROBADA'
    ESTADO_EN_REPARACION = 'EN_REPARACION'
    ESTADO_TERMINADA = 'TERMINADA'
    ESTADO_ENTREGADA = 'ENTREGADA'
    ESTADO_DIAGNOSTICO_RECHAZADO = 'DIAGNOSTICO_RECHAZADO'
    ESTADO_COTIZACION_RECHAZADA = 'COTIZACION_RECHAZADA'
    ESTADO_CANCELADA = 'CANCELADA'
    ESTADO_PAGADA = 'PAGADA'

    ESTADOS_ORDEN = [
        (ESTADO_NUEVA, 'Nueva'),
        (ESTADO_EN_DIAGNOSTICO, 'En Diagnóstico'),
        (ESTADO_COTIZADA, 'Cotizada'),
        (ESTADO_APROBADA, 'Aprobada'),
        (ESTADO_EN_REPARACION, 'En Reparación'),
        (ESTADO_TERMINADA, 'Terminada'),
        (ESTADO_ENTREGADA, 'Entregada'),
        (ESTADO_DIAGNOSTICO_RECHAZADO, 'Diagnóstico Rechazado'),
        (ESTADO_COTIZACION_RECHAZADA, 'Cotización Rechazada'),
        (ESTADO_CANCELADA, 'Cancelada'),
        (ESTADO_PAGADA, 'Pagada'),
    ]

    # Tipos de servicio
    TIPO_MECANICA = 'MECANICA'
    TIPO_LAMINADO_PINTURA = 'LAMINADO_PINTURA'
    TIPO_AFINACION = 'AFINACION'
    TIPO_FRENOS_SUSPENSION = 'FRENOS_SUSPENSION'
    TIPO_SISTEMA_ELECTRICO = 'SISTEMA_ELECTRICO'
    TIPO_OTRO = 'OTRO'

    TIPOS_SERVICIO = [
        (TIPO_MECANICA, '🔧 Mecánica General'),
        (TIPO_LAMINADO_PINTURA, '🎨 Laminado y Pintura'),
        (TIPO_AFINACION, '⚙️ Afinación'),
        (TIPO_FRENOS_SUSPENSION, '🛞 Frenos y Suspensión'),
        (TIPO_SISTEMA_ELECTRICO, '🔌 Sistema Eléctrico'),
        (TIPO_OTRO, '📋 Otro'),
    ]

    # Métodos de pago
    METODO_EFECTIVO = 'EFECTIVO'
    METODO_TRANSFERENCIA = 'TRANSFERENCIA'
    METODO_TARJETA = 'TARJETA'
    METODO_CHEQUE = 'CHEQUE'

    METODOS_PAGO = [
        (METODO_EFECTIVO, 'Efectivo'),
        (METODO_TRANSFERENCIA, 'Transferencia'),
        (METODO_TARJETA, 'Tarjeta'),
        (METODO_CHEQUE, 'Cheque'),
    ]

    # Identificación única
    numero_os = models.CharField(max_length=20, unique=True, editable=False)

    # Relaciones principales
    # Tipo de orden (Normal para clientes, Interna para motos del inventario)
    es_interna = models.BooleanField(default=False, help_text="¿Es una reparación para moto de nuestro inventario?")

    # Relaciones principales (Opcionales si es interna)
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='ordenes_servicio')
    vehiculo = models.ForeignKey('taller.Vehiculo', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='ordenes_servicio')

    # Relación para órdenes internas (Moto del inventario)
    vehiculo_inventario = models.ForeignKey('taller.VehiculoInventario', on_delete=models.SET_NULL,
                                            null=True, blank=True, related_name='ordenes_reparacion',
                                            help_text="Moto del inventario en reparación interna")

    mecanico_responsable = models.ForeignKey('taller.Mecanico', on_delete=models.SET_NULL,
                                             null=True, blank=True, related_name='ordenes_asignadas')

    # Tipo de servicio
    tipo_servicio = models.CharField(max_length=30, choices=TIPOS_SERVICIO, default=TIPO_MECANICA)

    # Fechas y kilometraje
    fecha_entrada = models.DateTimeField(auto_now_add=True)
    fecha_salida = models.DateTimeField(null=True, blank=True)
    kilometraje_entrada = models.PositiveIntegerField(null=True, blank=True)

    # Estado actual
    estado = models.CharField(max_length=30, choices=ESTADOS_ORDEN, default=ESTADO_NUEVA)

    # Diagnóstico
    costo_diagnostico = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    diagnostico_aplicado = models.BooleanField(default=False,
                                               help_text="¿Se cobró el costo de diagnóstico?")
    sintoma_cliente = models.TextField(blank=True, null=True,
                                       help_text="Lo que el cliente reporta")
    diagnostico_mecanico = models.TextField(blank=True, null=True,
                                            help_text="Lo que el mecánico encontró")

    # Notas técnicas
    notas_tecnicas = models.TextField(blank=True, null=True,
                                      help_text="Detalle de lo que se hizo o se hará")

    # Totales
    subtotal_refacciones = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal_mano_obra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                       verbose_name="Total Pagado", editable=False)
    # Pago y garantía
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, blank=True, null=True)
    garantia_dias = models.PositiveIntegerField(default=30,
                                                help_text="Días de garantía sobre la reparación")

    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "Orden de Servicio"
        verbose_name_plural = "Órdenes de Servicio"
        ordering = ['-fecha_entrada']

    def __str__(self):
        return f"{self.numero_os} - {self.cliente} - {self.vehiculo}"

    def save(self, *args, **kwargs):
        # Generar número de OS automático si es nuevo
        if not self.numero_os:
            ultimo_anio = self.fecha_entrada.year if self.fecha_entrada else 2026
            ultima_os = OrdenServicio.objects.filter(
                numero_os__startswith=f'OS-{ultimo_anio}-'
            ).order_by('-numero_os').first()

            if ultima_os:
                ultimo_numero = int(ultima_os.numero_os.split('-')[-1])
                nuevo_numero = ultimo_numero + 1
            else:
                nuevo_numero = 1

            self.numero_os = f'OS-{ultimo_anio}-{str(nuevo_numero).zfill(4)}'

        super().save(*args, **kwargs)


class ItemOrdenServicio(models.Model):
    """Modelo para los ítems de una orden de servicio (refacciones, materiales, mano de obra)"""

    # Tipos de ítem
    TIPO_REFACCION = 'REFACCION'
    TIPO_MATERIAL = 'MATERIAL'
    TIPO_MANO_OBRA = 'MANO_OBRA'

    TIPOS_ITEM = [
        (TIPO_REFACCION, '🔩 Refacción'),
        (TIPO_MATERIAL, ' Material'),
        (TIPO_MANO_OBRA, '👷 Mano de Obra'),
    ]

    # Relación con la orden
    orden_servicio = models.ForeignKey('taller.OrdenServicio', on_delete=models.CASCADE,
                                       related_name='items')

    # Relación con el Material (Producto) del inventario
    material = models.ForeignKey('materiales.Material', on_delete=models.PROTECT,
                                 null=True, blank=True, related_name='items_taller',
                                 help_text="Material o refacción utilizada del inventario")

    # Almacén de donde se tomará el material (solo para refacciones inventariables)
    almacen = models.ForeignKey('materiales.Almacen', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='items_taller',
                                help_text="Almacén de donde se descontará el stock")

    # Información del ítem
    tipo = models.CharField(max_length=20, choices=TIPOS_ITEM)
    descripcion = models.CharField(max_length=200,
                                   help_text="Descripción detallada (se llena automático si es material)")
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ítem de Orden"
        verbose_name_plural = "Ítems de Orden"
        ordering = ['tipo', 'descripcion']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descripcion}"

    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)


class PagoOrdenServicio(models.Model):
    """Modelo para registrar los pagos de una orden de servicio"""

    # Métodos de pago
    METODO_EFECTIVO = 'EFECTIVO'
    METODO_TRANSFERENCIA = 'TRANSFERENCIA'
    METODO_TARJETA = 'TARJETA'
    METODO_CHEQUE = 'CHEQUE'
    METODO_OTRO = 'OTRO'

    METODOS_PAGO = [
        (METODO_EFECTIVO, '💵 Efectivo'),
        (METODO_TRANSFERENCIA, '🏦 Transferencia'),
        (METODO_TARJETA, '💳 Tarjeta'),
        (METODO_CHEQUE, ' Cheque'),
        (METODO_OTRO, '🔹 Otro'),
    ]

    # Relación con la orden
    orden_servicio = models.ForeignKey('taller.OrdenServicio', on_delete=models.CASCADE,
                                       related_name='pagos',
                                       verbose_name="Orden de Servicio")

    # Información del pago
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto")
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, verbose_name="Método de Pago")
    referencia = models.CharField(max_length=100, blank=True,
                                  verbose_name="Referencia",
                                  help_text="No. de factura, transferencia, cheque, etc.")
    notas = models.TextField(blank=True, verbose_name="Notas")

    # Timestamps
    fecha_pago = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Pago")
    creado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                                   null=True, blank=True, verbose_name="Registrado por")

    class Meta:
        verbose_name = "Pago de Orden"
        verbose_name_plural = "Pagos de Órdenes"
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago de ${self.monto} - Orden {self.orden_servicio.numero_os}"


class VehiculoInventario(models.Model):
    """Modelo para gestionar el inventario de motos del taller (para venta)"""

    # Estados del vehículo en inventario
    ESTADO_NUEVO = 'NUEVO'
    ESTADO_SEMINUEVO = 'SEMINUEVO'
    ESTADO_EN_EXHIBICION = 'EXHIBICION'
    ESTADO_VENDIDO = 'VENDIDO'
    ESTADO_RESERVADO = 'RESERVADO'

    ESTADOS_INVENTARIO = [
        (ESTADO_NUEVO, ' Nuevo'),
        (ESTADO_SEMINUEVO, '♻️ Seminuevo'),
        (ESTADO_EN_EXHIBICION, '🏪 En Exhibición'),
        (ESTADO_VENDIDO, '✅ Vendido'),
        (ESTADO_RESERVADO, '🔒 Reservado'),
    ]

    # Información básica
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    año = models.PositiveIntegerField()
    color = models.CharField(max_length=30)
    cilindrada = models.PositiveIntegerField(help_text="Cilindrada en CC")

    # Identificación
    vin = models.CharField(max_length=17, unique=True, verbose_name="Número de Serie (VIN)",
                           help_text="Número de identificación vehicular")
    placa = models.CharField(max_length=20, blank=True, null=True)

    # Precios
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2,
                                        verbose_name="Precio de Compra")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2,
                                       verbose_name="Precio de Venta")

    # Estado y fechas
    estado = models.CharField(max_length=20, choices=ESTADOS_INVENTARIO, default=ESTADO_EN_EXHIBICION)
    fecha_ingreso = models.DateField(auto_now_add=True)
    fecha_venta = models.DateField(null=True, blank=True)

    # Costos reales (para calcular margen de ganancia real)
    costo_reparacion_interna = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                                   help_text="Suma de refacciones y mano de obra usada para repararla")

    @property
    def costo_total_real(self):
        """Costo final de la moto (Compra + Reparaciones)"""
        return self.precio_compra + self.costo_reparacion_interna

    # Notas
    notas = models.TextField(blank=True, null=True)

    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Moto en Inventario"
        verbose_name_plural = "Motos en Inventario"
        ordering = ['-fecha_ingreso']

    def __str__(self):
        return f"{self.marca} {self.modelo} {self.año} - {self.get_estado_display()}"
