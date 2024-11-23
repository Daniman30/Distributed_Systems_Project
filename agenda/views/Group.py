from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from agenda.models import Group, GroupMembership
from agenda.serializers import group

class GroupListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        groups = Group.objects.filter(members=request.user)
        serializer = group(groups, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        data['created_by'] = request.user.id
        serializer = group(data=data)
        if serializer.is_valid():
            group = serializer.save()
            GroupMembership.objects.create(group=group, user=request.user, role='admin')
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
