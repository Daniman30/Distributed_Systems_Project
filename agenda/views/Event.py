from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from agenda.models import Event, GroupMembership,Group
from agenda.serializers.event import EventSerializer

class EventListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Listar eventos personales confirmados
        personal_events = Event.objects.filter(
            participants=request.user,
            requires_acceptance=False
        ).exclude(group__isnull=False)  # Excluir eventos grupales

        # Listar eventos grupales confirmados donde el usuario ha aceptado
        group_events = Event.objects.filter(
            participants=request.user,
            requires_acceptance=False,
            accepted_by=request.user  # Solo mostrar si el usuario aceptó
        ).exclude(group__isnull=True)  # Excluir eventos personales

        personal_serializer = EventSerializer(personal_events, many=True)
        group_serializer = EventSerializer(group_events, many=True)

        return Response({
            "personal_events": personal_serializer.data,
            "group_events": group_serializer.data
        })

class EventCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        data['organizer'] = request.user.id

        group_id = data.get('group')
        participants = []

        # Validar si es un evento grupal
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
            except Group.DoesNotExist:
                return Response({"error": "El grupo especificado no existe."}, status=status.HTTP_404_NOT_FOUND)

            # Obtener los participantes del grupo
            participants = GroupMembership.objects.filter(group=group).values_list('user', flat=True)
            data['participants'] = list(participants)

            # Validar si el grupo es jerárquico y el creador es administrador
            is_hierarchical = group.is_hierarchical
            is_admin = GroupMembership.objects.filter(group=group, user=request.user, role='admin').exists()

            if is_hierarchical and is_admin:
                # Si es jerárquico y el creador es admin, no requiere aceptación y está aceptado por todos
                data['requires_acceptance'] = False
                accepted_by = list(participants)  # Aceptado automáticamente por todos
            else:
                # Si no es jerárquico o el creador no es admin, requiere aceptación
                data['requires_acceptance'] = True
                accepted_by = [request.user.id]  # Solo aceptado por el creador
        else:
            # Si es un evento personal
            participants = data.get('participants', [request.user.id])
            data['participants'] = participants

            # Requiere aceptación si tiene más de un participante
            data['requires_acceptance'] = len(participants) > 1
            accepted_by = [request.user.id]  # El creador lo acepta automáticamente

        serializer = EventSerializer(data=data)
        if serializer.is_valid():
            event = serializer.save()
            # Asignar participantes y aceptados
            event.participants.add(*data['participants'])
            event.accepted_by.add(*accepted_by)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class AcceptEventView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        try:
            # Verificar que el usuario es participante y que el evento requiere aceptación
            event = Event.objects.get(id=event_id, participants=request.user, requires_acceptance=True)
        except Event.DoesNotExist:
            return Response({"error": "El evento no requiere aceptación o no eres participante."}, status=status.HTTP_404_NOT_FOUND)

        # Añadir al usuario a la lista de aceptados
        event.accepted_by.add(request.user)

        # Verificar si todos los participantes han aceptado el evento
        if event.is_fully_accepted():
            event.requires_acceptance = False
            event.save()

            # Actualizar los participantes para que todos vean el evento como confirmado
            for participant in event.participants.all():
                # Aquí podrías agregar más lógica si necesitas notificar a los participantes
                pass

        return Response({"message": "Has aceptado el evento."}, status=status.HTTP_200_OK)


class CancelEventView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, event_id):
        try:
            # Verificar que el usuario es el organizador
            event = Event.objects.get(id=event_id, organizer=request.user)
        except Event.DoesNotExist:
            return Response({"error": "No tienes permiso para cancelar este evento."}, status=status.HTTP_404_NOT_FOUND)

        # Eliminar el evento
        event.delete()
        return Response({"message": "El evento ha sido cancelado."}, status=status.HTTP_204_NO_CONTENT)

class PendingEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filtrar eventos donde el usuario es participante y aún no ha aceptado
        pending_events = Event.objects.filter(
            participants=request.user,
            requires_acceptance=True
        ).exclude(accepted_by=request.user)
        pending_events = pending_events.exclude(organizer=request.user)

        # Serializar los eventos pendientes
        serializer = EventSerializer(pending_events, many=True)
        return Response(serializer.data)
