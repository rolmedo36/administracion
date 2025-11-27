# core/models.py
from django.db import models

class Empresa(models.Model):
    razon_social = models.CharField(max_length=200)
    nombre_comercial = models.CharField(max_length=200, blank=True)
    rfc = models.CharField("RFC", max_length=20, unique=True)
    regimen_fiscal = models.CharField("Régimen Fiscal", max_length=10, default="601")
    domicilio_calle = models.CharField("Calle", max_length=200)
    domicilio_numero = models.CharField("Número", max_length=20, blank=True)
    domicilio_colonia = models.CharField("Colonia", max_length=100)
    domicilio_ciudad = models.CharField("Ciudad", max_length=100)
    domicilio_estado = models.CharField("Estado", max_length=100)
    domicilio_pais = models.CharField("País", max_length=100, default="México")
    domicilio_cp = models.CharField("Código Postal", max_length=10)
    telefono = models.CharField("Teléfono", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    logo = models.ImageField(upload_to='empresa/', blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.razon_social

    def get_domicilio_completo(self):
        return f"{self.domicilio_calle} {self.domicilio_numero}, {self.domicilio_colonia}, {self.domicilio_ciudad}, {self.domicilio_estado} CP {self.domicilio_cp}"