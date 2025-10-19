# materiales/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Material, CategoriaMaterial
from .forms import MaterialForm, CategoriaMaterialForm

class MaterialListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Material
    template_name = 'materiales/material_list.html'
    context_object_name = 'materiales'
    permission_required = 'materiales.view_material'
    paginate_by = 10

    def get_queryset(self):
        queryset = Material.objects.all()
        categoria = self.request.GET.get('categoria')
        activo = self.request.GET.get('activo')
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        if activo is not None:
            queryset = queryset.filter(activo=(activo == '1'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaMaterial.objects.all()
        return context

class MaterialCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Material
    form_class = MaterialForm
    template_name = 'materiales/material_form.html'
    success_url = reverse_lazy('materiales:material_list')
    permission_required = 'materiales.add_material'

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        return super().form_valid(form)

class MaterialUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Material
    form_class = MaterialForm
    template_name = 'materiales/material_form.html'
    success_url = reverse_lazy('materiales:material_list')
    permission_required = 'materiales.change_material'

class MaterialDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Material
    template_name = 'materiales/material_confirm_delete.html'
    success_url = reverse_lazy('materiales:material_list')
    permission_required = 'materiales.delete_material'

# materiales/views.py (agrega al final)


class CategoriaMaterialListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = CategoriaMaterial
    template_name = 'materiales/categoria_list.html'
    context_object_name = 'categorias'
    permission_required = 'materiales.view_categoriamaterial'
    ordering = ['nombre']

class CategoriaMaterialCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = CategoriaMaterial
    form_class = CategoriaMaterialForm
    template_name = 'materiales/categoria_form.html'
    success_url = reverse_lazy('materiales:categoria_list')
    permission_required = 'materiales.add_categoriamaterial'

class CategoriaMaterialUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = CategoriaMaterial
    form_class = CategoriaMaterialForm
    template_name = 'materiales/categoria_form.html'
    success_url = reverse_lazy('materiales:categoria_list')
    permission_required = 'materiales.change_categoriamaterial'

class CategoriaMaterialDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = CategoriaMaterial
    template_name = 'materiales/categoria_confirm_delete.html'
    success_url = reverse_lazy('materiales:categoria_list')
    permission_required = 'materiales.delete_categoriamaterial'

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except models.ProtectedError:
            messages.error(request, "No se puede eliminar esta categoría porque está asociada a uno o más materiales.")
            return redirect(self.success_url)

