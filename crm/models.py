from django.db import models
from django.contrib.auth.models import User
from clientes.models import Cliente

# Choices
ESTADO_PROSPECTO_CHOICES = [
    ('nuevo', 'Nuevo'),
    ('contactado', 'Contactado'),
    ('no_calificado', 'No Calificado'),
    ('calificado', 'Calificado'),
]

ORIGEN_PROSPECTO_CHOICES = [
    ('web', 'Formulario Web'),
    ('referido', 'Referido'),
    ('evento', 'Evento'),
    ('llamada', 'Llamada Fría'),
    ('redes', 'Redes Sociales'),
    ('otro', 'Otro'),
]

ETAPA_OPORTUNIDAD_CHOICES = [
    ('prospecto', 'Prospecto'),
    ('contacto', 'Contacto Inicial'),
    ('necesidades', 'Análisis de Necesidades'),
    ('propuesta', 'Propuesta Enviada'),
    ('negociacion', 'Negociación'),
    ('ganado', 'Cierre Ganado'),
    ('perdido', 'Cierre Perdido'),
]

TIPO_ACTIVIDAD_CHOICES = [
    ('llamada', 'Llamada'),
    ('email', 'Email'),
    ('reunion', 'Reunión'),
    ('tarea', 'Tarea'),
    ('nota', 'Nota'),
]

ESTADO_ACTIVIDAD_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('completada', 'Completada'),
    ('cancelada', 'Cancelada'),
]


class Prospecto(models.Model):
    nombre = models.CharField(max_length=200)
    empresa = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=100, blank=True)
    origen = models.CharField(max_length=20, choices=ORIGEN_PROSPECTO_CHOICES, default='web')
    estado = models.CharField(max_length=20, choices=ESTADO_PROSPECTO_CHOICES, default='nuevo')
    fecha_proximo_contacto = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True)
    asignado_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='prospectos_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Prospecto"
        verbose_name_plural = "Prospectos"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre} - {self.empresa}"


class Oportunidad(models.Model):
    prospecto = models.ForeignKey(Prospecto, on_delete=models.SET_NULL, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    monto_estimado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    etapa = models.CharField(max_length=20, choices=ETAPA_OPORTUNIDAD_CHOICES, default='prospecto')
    probabilidad = models.PositiveIntegerField(default=0, help_text="Porcentaje de probabilidad de cierre")
    fecha_cierre_estimada = models.DateField(null=True, blank=True)
    fecha_proximo_contacto = models.DateTimeField(null=True, blank=True)
    asignado_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='oportunidades_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Oportunidad"
        verbose_name_plural = "Oportunidades"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre


class Actividad(models.Model):
    tipo = models.CharField(max_length=20, choices=TIPO_ACTIVIDAD_CHOICES)
    asunto = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_hora = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_ACTIVIDAD_CHOICES, default='pendiente')
    completada_fecha = models.DateTimeField(null=True, blank=True)

    # Relaciones
    prospecto = models.ForeignKey(Prospecto, on_delete=models.CASCADE, null=True, blank=True)
    oportunidad = models.ForeignKey(Oportunidad, on_delete=models.CASCADE, null=True, blank=True)
    relacionado_con = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='actividades_programadas'
    )

    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='actividades_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"
        ordering = ['fecha_hora']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.asunto}"


class PlantillaEmail(models.Model):
    nombre = models.CharField(max_length=100)
    asunto = models.CharField(max_length=200)
    cuerpo = models.TextField(help_text="Puedes usar {{ nombre }} para personalizar")
    categoria = models.CharField(max_length=50, blank=True)
    activa = models.BooleanField(default=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Plantilla de Email"
        verbose_name_plural = "Plantillas de Email"

    def __str__(self):
        return self.nombre