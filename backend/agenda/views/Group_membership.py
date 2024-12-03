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
class RemoveMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, group_id, user_id):
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({"error": "El grupo no existe."}, status=status.HTTP_404_NOT_FOUND)

        # Verificar que el usuario autenticado es administrador
        is_admin = GroupMembership.objects.filter(group=group, user=request.user, role='admin').exists()
        if not is_admin:
            return Response({"error": "No tienes permisos para eliminar miembros de este grupo."}, status=status.HTTP_403_FORBIDDEN)

        # Verificar que el miembro existe en el grupo
        try:
            membership = GroupMembership.objects.get(group=group, user_id=user_id)
        except GroupMembership.DoesNotExist:
            return Response({"error": "El usuario no pertenece al grupo."}, status=status.HTTP_404_NOT_FOUND)

        # Eliminar al miembro
        membership.delete()
        return Response({"message": "Miembro eliminado correctamente."}, status=status.HTTP_204_NO_CONTENT)
class LeaveGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, group_id):
        try:
            membership = GroupMembership.objects.get(group_id=group_id, user=request.user)
        except GroupMembership.DoesNotExist:
            return Response({"error": "No perteneces a este grupo."}, status=status.HTTP_404_NOT_FOUND)

        # Verificar que no es el último administrador
        if membership.role == 'admin':
            admins_count = GroupMembership.objects.filter(group_id=group_id, role='admin').count()
            if admins_count == 1:
                return Response({"error": "No puedes abandonar el grupo como único administrador."}, status=status.HTTP_403_FORBIDDEN)

        # Eliminar la membresía del grupo
        membership.delete()
        return Response({"message": "Has salido del grupo."}, status=status.HTTP_204_NO_CONTENT)

