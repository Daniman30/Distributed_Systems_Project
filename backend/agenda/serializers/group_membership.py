from rest_framework import serializers
from agenda.models import GroupMembership, Group, User

class AddMemberSerializer(serializers.ModelSerializer):
    group_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=[('admin', 'Admin'), ('member', 'Member')], default='member')

    class Meta:
        model = GroupMembership
        fields = ['group_id', 'user_id', 'role']

    def validate(self, data):
        # Validar si el grupo existe
        try:
            group = Group.objects.get(id=data['group_id'])
        except Group.DoesNotExist:
            raise serializers.ValidationError('El grupo no existe.')

        # Validar si el usuario ya es miembro del grupo
        if GroupMembership.objects.filter(group=group, user_id=data['user_id']).exists():
            raise serializers.ValidationError('El usuario ya es miembro del grupo.')

        return data

    def create(self, validated_data):
        # Añadir al miembro al grupo
        group = Group.objects.get(id=validated_data['group_id'])
        user = User.objects.get(id=validated_data['user_id'])
        return GroupMembership.objects.create(
            group=group,
            user=user,
            role=validated_data['role']
        )
