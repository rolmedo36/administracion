from .models import Empresa

def empresa_context(request):
    empresa = Empresa.objects.first()
    return {
        'empresa_nombre': empresa.razon_social if empresa else 'Sistema Administrativo',
        'empresa': empresa
    }