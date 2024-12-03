from django.shortcuts import render

def index(request):
    return render(request, 'index.html', {'titulo': 'Inicio'})

def login(request):
    return render(request, 'login.html')

def register(request):
    return render(request, 'register.html')

def forgot(request):
    return render(request, 'forgot.html')