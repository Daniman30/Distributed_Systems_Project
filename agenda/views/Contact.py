from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from agenda.models import Contact
from agenda.serializers import contact

class ContactListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        contacts = Contact.objects.filter(owner=request.user)
        serializer = contact.ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        data['owner'] = request.user.id
        serializer = contact.ContactSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
