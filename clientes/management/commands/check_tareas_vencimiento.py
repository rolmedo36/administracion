from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone
from clientes.models import ActividadCliente
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Revisa tareas próximas a vencer y envía notificaciones por correo'

    def handle(self, *args, **options):
        # 1. Definir el umbral: tareas que vencen en las próximas 24 horas
        ahora = timezone.now()
        umbral = ahora + timezone.timedelta(hours=24)

        # 2. Buscar tareas pendientes que vencen en las próximas 24 horas
        tareas_proximas = ActividadCliente.objects.filter(
            tipo='tarea',
            estado='pendiente',
            fecha_programada__lte=umbral,
            fecha_programada__gte=ahora
        )

        # 3. Enviar notificación por cada tarea encontrada
        for tarea in tareas_proximas:
            if tarea.creado_por and tarea.creado_por.email:
                # 4. Preparar el correo
                subject = f"⚠️ Tarea Próxima a Vencer: {tarea.titulo}"
                message = (
                    f"¡Hola {tarea.creado_por.get_full_name() or 'Equipo'}!\n\n"
                    f"La siguiente tarea está próxima a vencer:\n\n"
                    f"• Cliente: {tarea.cliente.nombre}\n"
                    f"• Título: {tarea.titulo}\n"
                    f"• Programada para: {tarea.fecha_programada.strftime('%d/%m/%Y %H:%M')}\n\n"
                    f"¡No olvides completarla a tiempo!\n\n"
                    f"---\n"
                    f"Este correo fue generado automáticamente por el sistema de NCP Software."
                )

                # 5. Enviar el correo
                send_mail(
                    subject,
                    message,
                    'NCP Software <contacto@ncp.com.mx>',
                    [tarea.creado_por.email],
                    fail_silently=False,
                )

                self.stdout.write(
                    self.style.SUCCESS(f"Correo enviado a {tarea.creado_por.email} por tarea: {tarea.titulo}")
                )

        # 6. Mensaje final
        self.stdout.write(
            self.style.SUCCESS(f"Revisadas {tareas_proximas.count()} tareas próximas a vencer")
        )