from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import CustomUserCreationForm
from .models import CustomUser

def homepage(request):
    return render(request, 'homepage.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # No guarda el modelo aún

            if(CustomUser.objects.count() == 0):
                user.user_type = 'BOSS'
            
            user.save()  # Guarda el usuario
            login(request, user)
            messages.success(request, 'Te has registrado correctamente.')
            return redirect('homepage')  # Redirecciona a la vista principal (debes definirla)
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('users:user_homepage')  # Redirecciona a la vista principal (debes definirla)
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrecta')
    return render(request, 'users/login.html')

def user_homepage_view(request):
    if request.user.is_authenticated:
        return render(request, 'users/user_homepage.html')
    else:
        messages.error(request, 'Por favor, inicia sesión para acceder a esta página.')
        return redirect('users:login')

def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión.')
    return redirect('homepage')  # Redirecciona a la vista de inicio de sesión
