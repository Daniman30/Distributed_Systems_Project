from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from agenda.models import Contact
from agenda.serializers import contact
from rest_framework import status

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
class DeleteContactView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, contact_id):
        try:
            contact = Contact.objects.get(id=contact_id, owner=request.user)
        except Contact.DoesNotExist:
            return Response({"error": "Contacto no encontrado o no pertenece a este usuario."}, status=status.HTTP_404_NOT_FOUND)

        # Eliminar el contacto
        contact.delete()
        return Response({"message": "Contacto eliminado correctamente."}, status=status.HTTP_204_NO_CONTENT)

