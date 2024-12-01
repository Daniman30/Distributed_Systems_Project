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
from agenda.views import Register, Contact,Group,Group_membership,Event,views,Agenda

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', Register.log_in, name='login'),
    path('register/', Register.sign_up, name='register'),
    path('forgot/', views.forgot, name='forgot'),
   
    re_path("test_token", Register.test_token),
    path('contacts/', Contact.ContactListCreateView.as_view(), name='contacts'),
    path('groups/', Group.GroupListCreateView.as_view(), name='groups'),
    path('groups/add-member/', Group_membership.AddMemberView.as_view(), name='add-member'),
    path('groups/<int:group_id>/delete/', Group.DeleteGroupView.as_view(), name='delete-group'),
    path('groups/<int:group_id>/remove-member/<int:user_id>/', Group_membership.RemoveMemberView.as_view(), name='remove-member'),
    path('contacts/<int:contact_id>/delete/', Contact.DeleteContactView.as_view(), name='delete-contact'),
    path('groups/<int:group_id>/leave/', Group_membership.LeaveGroupView.as_view(), name='leave-group'),
    path('events/<int:event_id>/accept/', Event.AcceptEventView.as_view(), name='accept-event'),
    path('events/<int:event_id>/cancel/', Event.CancelEventView.as_view(), name='cancel-event'),
    path('events/', Event.EventListView.as_view(), name='list-events'),
    path('events/create/', Event.EventCreateView.as_view(), name='create-event'),
    path('events/pending/', Event.PendingEventsView.as_view(), name='pending-events'),
    path('agendas/', Agenda.AgendaView.as_view(), name='agendas'),
]
