from django.contrib import admin

# Register your models here.


from django.contrib import admin
from .models import User, Contact, Group, GroupMembership, Event

# Registro del modelo Contact
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('owner', 'contact', 'created_at')
    search_fields = ('owner__username', 'contact__username')
    list_filter = ('owner',)


# Registro del modelo Group
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_by', 'is_hierarchical')
    search_fields = ('name', 'description', 'created_by__username')
    list_filter = ('is_hierarchical',)
    readonly_fields = ('created_by',)


# Registro del modelo GroupMembership
@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('group', 'user', 'role')
    search_fields = ('group__name', 'user__username')
    list_filter = ('role',)


# Registro del modelo Event
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'start_time', 'end_time', 'privacy', 'group', 'requires_acceptance')
    search_fields = ('title', 'organizer__username', 'group__name')
    list_filter = ('privacy', 'requires_acceptance')
    readonly_fields = ('organizer',)
    filter_horizontal = ('participants', 'accepted_by')

    def list_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    list_participants.short_description = 'Participants'


# Registro del modelo User (si es necesario personalizarlo)
# Si estás usando el modelo de usuario predeterminado de Django, no necesitas registrarlo aquí.
