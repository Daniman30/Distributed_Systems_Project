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
from django.urls import path,re_path
from agenda.views import Register, Contact,Group,Group_membership

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path("log_in", Register.log_in),
    re_path("sign_up", Register.sign_up),
    re_path("test_token", Register.test_token),
    path('contacts/', Contact.ContactListCreateView.as_view(), name='contacts'),
    path('groups/', Group.GroupListCreateView.as_view(), name='groups'),
    path('groups/add-member/', Group_membership.AddMemberView.as_view(), name='add-member'),
]
