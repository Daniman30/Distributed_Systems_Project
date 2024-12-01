from rest_framework import serializers
from agenda.models import Contact

class ContactSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.username', read_only=True)
    class Meta:
        model = Contact
        fields = ['id', 'owner', 'contact','contact_name', 'created_at'] 
