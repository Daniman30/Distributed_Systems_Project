from django.shortcuts import render

def index(request):
    return render(request, 'agenda/index.html', {'titulo': 'Inicio'})

def login(request):
    return render(request, 'agenda/login.html')

def register(request):
    return render(request, 'agenda/register.html')

def forgot(request):
    return render(request, 'agenda/forgot.html')