from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from agenda.models import Event, GroupMembership,Group
from agenda.serializers.event import EventSerializer

class EventListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Eventos personales
        personal_events = Event.objects.filter(organizer=request.user)

        # Eventos grupales
        group_events = Event.objects.filter(group__members=request.user)

        # Serializar y combinar resultados
        personal_serializer = EventSerializer(personal_events, many=True)
        group_serializer = EventSerializer(group_events, many=True)

        return Response({
            "personal_events": personal_serializer.data,
            "group_events": group_serializer.data,
        })

class EventCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        data['organizer'] = request.user.id

        group_id = data.get('group')
        participants = data.get('participants', [])

        # Si no hay participantes, el organizador es el único participante
        if not participants:
            participants = [request.user.id]

        requires_acceptance = False  # Inicialmente no requiere aceptación

        # Validar si es un evento grupal
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
            except Group.DoesNotExist:
                return Response({"error": "El grupo especificado no existe."}, status=status.HTTP_404_NOT_FOUND)

            # Verificar membresía
            if not GroupMembership.objects.filter(group=group, user=request.user).exists():
                return Response({"error": "No perteneces al grupo especificado."}, status=status.HTTP_403_FORBIDDEN)

            # Verificar si es admin en un grupo jerárquico
            is_admin = GroupMembership.objects.filter(group=group, user=request.user, role='admin').exists()
            if not (group.is_hierarchical and is_admin):
                requires_acceptance = True  # Requiere aceptación si no es admin en grupo jerárquico
        else:
            # Evento personal requiere aceptación si tiene más de un participante
            if len(participants) > 1:
                requires_acceptance = True

        data['requires_acceptance'] = requires_acceptance

        serializer = EventSerializer(data=data)
        if serializer.is_valid():
            event = serializer.save()

            # Añadir participantes
            event.participants.add(*participants)

            # Aceptación automática si es admin en grupo jerárquico
            if group_id and group.is_hierarchical and is_admin:
                event.accepted_by.add(*participants)

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
