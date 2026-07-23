from django.db import models
from django.contrib.auth.models import User

# Choices
TIPO_CLIENTE_CHOICES = [
    ('fisica', 'Persona Física'),
    ('moral', 'Persona Moral'),
]

REGIMEN_FISCAL_CHOICES = [
    ('601', 'General de Ley Personas Morales'),
    ('603', 'Personas Morales con Fines no Lucrativos'),
    ('605', 'Sueldos y Salarios e Ingresos Asimilados a Salarios'),
    ('606', 'Arrendamiento'),
    ('607', 'Régimen de Enajenación o Adquisición de Bienes'),
    ('608', 'Demás ingresos'),
    ('610', 'Residentes en el Extranjero sin Establecimiento Permanente en México'),
    ('611', 'Ingresos por Dividendos (socios y accionistas)'),
    ('612', 'Personas Físicas con Actividades Empresariales y Profesionales'),
    ('614', 'Ingresos por intereses'),
    ('615', 'Régimen de los ingresos por obtención de premios'),
    ('616', 'Sin obligaciones fiscales'),
    ('620', 'Sociedades Cooperativas de Producción que optan por diferir sus ingresos'),
    ('621', 'Régimen de Incorporación Fiscal'),
    ('622', 'Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras'),
    ('623', 'Opcional para Grupos de Sociedades'),
    ('624', 'Coordinados'),
    ('625', 'Régimen de las Actividades Empresariales con Ingresos a través de Plataformas Tecnológicas'),
    ('626', 'Régimen Simplificado de Confianza'),
]

USO_CFDI_CHOICES = [
    ('G01', 'Adquisición de mercancías'),
    ('G02', 'Devoluciones, descuentos o bonificaciones'),
    ('G03', 'Gastos en general'),
    ('I01', 'Construcciones'),
    ('I02', 'Mobilario y equipo de oficina por inversiones'),
    ('I03', 'Equipo de transporte'),
    ('I04', 'Equipo de cómputo y accesorios'),
    ('I05', 'Dados, troqueles, moldes, matrices y herramental'),
    ('I06', 'Comunicaciones telefónicas'),
    ('I07', 'Comunicaciones satelitales'),
    ('I08', 'Otra maquinaria y equipo'),
    ('D01', 'Honorarios médicos, dentales y gastos hospitalarios'),
    ('D02', 'Gastos médicos por incapacidad o discapacidad'),
    ('D03', 'Gastos funerales'),
    ('D04', 'Donativos'),
    ('D05', 'Intereses reales efectivamente pagados por créditos hipotecarios'),
    ('D06', 'Aportaciones voluntarias al SAR'),
    ('D07', 'Primas por seguros de gastos médicos'),
    ('D08', 'Gastos de transportación escolar obligatoria'),
    ('D09', 'Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones'),
    ('D10', 'Pagos por servicios educativos (colegiaturas)'),
    ('S01', 'Sin efectos fiscales'),
    ('CP01', 'Pagos'),
    ('CN01', 'Nómina'),
]

MONEDA_CHOICES = [
    ('MXN', 'Pesos Mexicanos'),
    ('USD', 'Dólares Americanos'),
    ('EUR', 'Euros'),
]

CLASIFICACION_CLIENTE_CHOICES = [
    ('A', 'Clase A (Alto volumen)'),
    ('B', 'Clase B (Medio volumen)'),
    ('C', 'Clase C (Bajo volumen)'),
]


class Cliente(models.Model):
    # Información básica
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)
    nombre_comercial = models.CharField(max_length=200, blank=True)
    tipo_cliente = models.CharField(max_length=20, choices=TIPO_CLIENTE_CHOICES)

    # Identificación fiscal
    rfc = models.CharField("RFC", max_length=20, unique=True)
    curp = models.CharField("CURP", max_length=20, blank=True)
    regimen_fiscal = models.CharField(max_length=10, choices=REGIMEN_FISCAL_CHOICES)
    uso_cfdi = models.CharField("Uso CFDI", max_length=10, choices=USO_CFDI_CHOICES)

    # Contacto
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    telefono_movil = models.CharField(max_length=20, blank=True)
    contacto_nombre = models.CharField("Nombre de contacto", max_length=100, blank=True)

    # Dirección fiscal
    calle = models.CharField(max_length=200)
    colonia = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    pais = models.CharField(max_length=100, default="México")
    codigo_postal = models.CharField(max_length=10)

    # Condiciones comerciales
    limite_credito = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    dias_credito = models.PositiveIntegerField(default=0)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Porcentaje de descuento")
    moneda = models.CharField(max_length=10, choices=MONEDA_CHOICES, default='MXN')
    clasificacion = models.CharField(max_length=10, choices=CLASIFICACION_CLIENTE_CHOICES, default='C')

    # Control
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    vendedores_asignados = models.ManyToManyField(
        'ventas.Vendedor',
        blank=True,
        related_name='clientes_asignados'
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def get_clasificacion_display_full(self):
        return dict(CLASIFICACION_CLIENTE_CHOICES).get(self.clasificacion, self.clasificacion)

class ActividadCliente(models.Model):
    class TipoActividad(models.TextChoices):
        COMENTARIO = 'comentario', 'Comentario'
        TAREA = 'tarea', 'Tarea Pendiente'
        EVENTO = 'evento', 'Evento / Reunión'

    class EstadoActividad(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        COMPLETADA = 'completada', 'Completada'
        CANCELADA = 'cancelada', 'Cancelada'

    # Relación con el cliente (Ajusta el 'on_delete' y la importación según tu modelo real)
    cliente = models.ForeignKey(
        'clientes.Cliente',  # <--- CAMBIA ESTO por la ruta real de tu modelo Cliente
        on_delete=models.CASCADE,
        related_name='actividades'
    )

    tipo = models.CharField(
        max_length=20,
        choices=TipoActividad.choices,
        default=TipoActividad.COMENTARIO
    )

    titulo = models.CharField(max_length=255, help_text="Resumen corto de la actividad")
    descripcion = models.TextField(blank=True, null=True)

    # Fecha y hora (Obligatoria para tareas y eventos)
    fecha_programada = models.DateTimeField(blank=True, null=True)

    estado = models.CharField(
        max_length=20,
        choices=EstadoActividad.choices,
        default=EstadoActividad.PENDIENTE
    )

    es_privado = models.BooleanField(
        default=True,
        help_text="Si es True, solo el equipo interno puede verlo."
    )

    notificacion_enviada = models.BooleanField(default=False)

    # Auditoría
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_programada', '-fecha_creacion']  # Ordena por fecha más reciente
        verbose_name = "Actividad de Cliente"
        verbose_name_plural = "Actividades de Clientes"

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo} - {self.cliente}"


class DocumentoCliente(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('rfc', 'RFC / Constancia de Situación Fiscal'),
        ('contrato', 'Contrato de Servicios'),
        ('comprobante_domicilio', 'Comprobante de Domicilio'),
        ('acta_constitutiva', 'Acta Constitutiva'),
        ('otro', 'Otro'),
    ]

    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.CASCADE,
        related_name='documentos'
    )
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_DOCUMENTO_CHOICES,
        default='otro'
    )
    archivo = models.FileField(
        upload_to='documentos_clientes/%Y/%m/',
        help_text="Formatos permitidos: PDF, JPG, PNG"
    )
    descripcion = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Ej: Contrato firmado versión 2024"
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Documento de Cliente"
        verbose_name_plural = "Documentos de Clientes"
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente.nombre}"