from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime

from .models import Actividad, PlantillaEmail


def enviar_email_actividad(actividad):
    """Envía un email basado en la actividad y su plantilla."""
    if actividad.tipo != 'email':
        return False

    try:
        # Obtener el email del prospecto o cliente relacionado
        email_destino = None
        contexto = {}

        if actividad.prospecto:
            email_destino = actividad.prospecto.email
            contexto = {
                'nombre': actividad.prospecto.nombre,
                'empresa': actividad.prospecto.empresa,
                'fecha': datetime.now().strftime('%d/%m/%Y')
            }
        elif actividad.oportunidad:
            if actividad.oportunidad.cliente:
                email_destino = actividad.oportunidad.cliente.email
                contexto = {
                    'nombre': actividad.oportunidad.cliente.nombre,
                    'empresa': actividad.oportunidad.cliente.nombre_comercial,
                    'fecha': datetime.now().strftime('%d/%m/%Y')
                }
            elif actividad.oportunidad.prospecto:
                email_destino = actividad.oportunidad.prospecto.email
                contexto = {
                    'nombre': actividad.oportunidad.prospecto.nombre,
                    'empresa': actividad.oportunidad.prospecto.empresa,
                    'fecha': datetime.now().strftime('%d/%m/%Y')
                }

        if not email_destino:
            return False

        # Usar la primera plantilla activa
        plantilla = PlantillaEmail.objects.filter(activa=True).first()

        if plantilla:
            asunto = plantilla.asunto
            # Personalizar el cuerpo con el contexto
            cuerpo = plantilla.cuerpo
            for key, value in contexto.items():
                if value:
                    cuerpo = cuerpo.replace(f'{{{{ {key} }}}}', str(value))
        else:
            asunto = f"Actividad: {actividad.asunto}"
            cuerpo = actividad.descripcion or "No hay descripción."

        send_mail(
            asunto,
            cuerpo,
            settings.DEFAULT_FROM_EMAIL,
            [email_destino],
            fail_silently=False,
        )

        return True
    except Exception as e:
        print(f"Error al enviar email: {e}")
        return False