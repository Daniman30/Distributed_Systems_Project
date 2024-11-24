from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from agenda.models import Group, GroupMembership
from agenda.serializers.group import GroupSerializer
from rest_framework import status

class GroupListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        groups = Group.objects.filter(members=request.user)
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        data['created_by'] = request.user.id
        serializer = GroupSerializer(data=data)
        if serializer.is_valid():
            group = serializer.save()
            GroupMembership.objects.create(group=group, user=request.user, role='admin')
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
    def delete(self, request, group_id):
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({"error": "El grupo no existe."}, status=status.HTTP_404_NOT_FOUND)

        # Verificar que el usuario es administrador
        is_admin = GroupMembership.objects.filter(group=group, user=request.user, role='admin').exists()
        if not is_admin:
            return Response({"error": "No tienes permisos para eliminar este grupo."}, status=status.HTTP_403_FORBIDDEN)

        # Eliminar el grupo
        group.delete()
