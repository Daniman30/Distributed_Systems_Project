from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from agenda.serializers.group_membership import AddMemberSerializer
from agenda.models import Group, GroupMembership

class AddMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddMemberSerializer(data=request.data)
        if serializer.is_valid():
            # Validar que el usuario autenticado sea admin del grupo
            group = Group.objects.get(id=serializer.validated_data['group_id'])
            if not GroupMembership.objects.filter(group=group, user=request.user, role='admin').exists():
                return Response({'error': 'No tienes permisos para añadir miembros.'}, status=status.HTTP_403_FORBIDDEN)
            
            # Guardar el nuevo miembro
            member = serializer.save()
            return Response({
                'message': f'{member.user.username} añadido al grupo {member.group.name} como {member.role}.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
