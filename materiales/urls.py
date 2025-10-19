# materiales/urls.py
from django.urls import path
from . import views

app_name = 'materiales'

urlpatterns = [
    # Materiales
    path('', views.MaterialListView.as_view(), name='material_list'),
    path('crear/', views.MaterialCreateView.as_view(), name='material_create'),
    path('<int:pk>/editar/', views.MaterialUpdateView.as_view(), name='material_update'),
    path('<int:pk>/eliminar/', views.MaterialDeleteView.as_view(), name='material_delete'),

    # Categorías
    path('categorias/', views.CategoriaMaterialListView.as_view(), name='categoria_list'),
    path('categorias/crear/', views.CategoriaMaterialCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaMaterialUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/eliminar/', views.CategoriaMaterialDeleteView.as_view(), name='categoria_delete'),
]