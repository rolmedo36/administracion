from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

# === LOGIN ===
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Bienvenido, {user.username}!")
            return redirect('/')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    return render(request, 'accounts/login.html')

# === LOGOUT ===
@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, "Sesión cerrada exitosamente.")
        return redirect('accounts:login')
    return render(request, 'accounts/logout.html')

# === REGISTRO ===
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Usuario {user.username} creado exitosamente.")
            return redirect('accounts:login')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

# === LISTA DE USUARIOS ===
@login_required
@permission_required('auth.view_user', raise_exception=True)
def user_list(request):
    users = User.objects.all().order_by('username')
    return render(request, 'accounts/user_list.html', {'users': users})

# === CREAR USUARIO ===
@login_required
@permission_required('auth.add_user', raise_exception=True)
def user_create(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Usuario {user.username} creado exitosamente.")
            return redirect('accounts:user_list')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/user_form.html', {'form': form})

# === EDITAR USUARIO ===
@login_required
@permission_required('auth.change_user', raise_exception=True)
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Usuario {user.username} actualizado.")
            return redirect('accounts:user_list')
    else:
        form = UserChangeForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'object': user})

# === ELIMINAR USUARIO ===
@login_required
@permission_required('auth.delete_user', raise_exception=True)
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f"Usuario {username} eliminado.")
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'object': user})