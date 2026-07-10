from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from .models import Empresa
from .forms import EmpresaForm

@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html', {
        'menu_template': 'core/menus/menu_completo.html',
    })

@login_required
@permission_required('core.change_empresa', raise_exception=True)
def empresa_update(request):
    empresa = Empresa.objects.first()  # Solo permitimos una empresa
    if not empresa:
        empresa = Empresa.objects.create(
            razon_social="Nueva Empresa",
            rfc="XAXX010101000",
            domicilio_calle="Calle Principal",
            domicilio_colonia="Centro",
            domicilio_ciudad="Ciudad",
            domicilio_estado="Estado",
            domicilio_cp="00000"
        )

    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, "Datos de la empresa actualizados exitosamente.")
            return redirect('core:dashboard')
    else:
        form = EmpresaForm(instance=empresa)

    return render(request, 'core/empresa_form.html', {'form': form, 'object': empresa})