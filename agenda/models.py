from django.contrib.auth.models import User
from django.db import models

class Contact(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    contact = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_by')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.owner.username} -> {self.contact.username}"

class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_hierarchical = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, through='GroupMembership')

    def __str__(self):
        return self.name

class GroupMembership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=[('admin', 'Admin'), ('member', 'Member')], default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    

class Event(models.Model):
    PRIVACY_CHOICES = [
        ('public', 'Público'),
        ('private', 'Privado'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='private')
    group = models.ForeignKey('Group', on_delete=models.CASCADE, blank=True, null=True, related_name='events')
    participants = models.ManyToManyField(User, related_name='participating_events')
    requires_acceptance = models.BooleanField(default=False)  # Solo aplica para grupos no jerárquicos
    accepted_by = models.ManyToManyField(User, related_name='accepted_events', blank=True)

    def is_conflicting(self, start, end):
        return self.start_time < end and self.end_time > start

    def is_fully_accepted(self):
        if not self.requires_acceptance:
            return True
        return self.participants.count() == self.accepted_by.count()
