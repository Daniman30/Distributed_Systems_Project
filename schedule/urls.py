"""
URL configuration for schedule project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path,re_path
from agenda.views import Register


urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include('agenda.urls')),
    path('log_in/', Register.log_in, name='log_in'),
    re_path("sign_up", Register.sign_up),
    re_path("test_token", Register.test_token),
]
