from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from agenda.models import Contact
from agenda.serializers import contact

class GetUserIdView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')

        # Verificar que ambos campos se proporcionen
        if not username or not email:
            return Response({"error": "Se requieren 'username' y 'email'."}, status=400)

        try:
            # Buscar el usuario por username y email
            user = User.objects.get(username=username, email=email)
            return Response({"id": user.id}, status=200)
        except User.DoesNotExist:
            return Response({"error": "Usuario no encontrado."}, status=404)
