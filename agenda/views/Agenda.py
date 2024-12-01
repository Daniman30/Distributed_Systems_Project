from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from agenda.models import Event, Group, GroupMembership
from agenda.serializers.event import EventSerializer
from datetime import datetime

class AgendaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        group_id = request.query_params.get('group_id')

        if not start_date or not end_date:
            return Response({"error": "Se deben proporcionar las fechas de inicio y fin."}, status=400)

        try:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
        except ValueError:
            return Response({"error": "Las fechas deben estar en formato ISO."}, status=400)

        # Obtener eventos dentro del rango de fechas
        events = Event.objects.filter(
            start_time__gte=start_date,
            end_time__lte=end_date
        )

        # Filtrar eventos del grupo si se especifica
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                events = events.filter(group=group)
            except Group.DoesNotExist:
                return Response({"error": "El grupo especificado no existe."}, status=404)

        # Crear la respuesta combinada
        timeline = []
        for event in events:
            if event.privacy == "public" or request.user in event.participants.all():
                timeline.append({
                    "id": event.id,
                    "title": event.title,
                    "description": event.description,
                    "start_time": event.start_time,
                    "end_time": event.end_time,
                    "organizer": event.organizer.username,
                    "group": event.group.name if event.group else None,
                    "privacy": event.privacy,
                    "status": "ocupado"
                })
            else:
                # Mostrar solo que el horario está ocupado
                timeline.append({
                    "id": event.id,
                    "title": "Ocupado",
                    "description": None,
                    "start_time": event.start_time,
                    "end_time": event.end_time,
                    "organizer": None,
                    "group": event.group.name if event.group else None,
                    "privacy": event.privacy,
                    "status": "ocupado"
                })

        return Response(timeline)
    
class GroupMemberAgendaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Validar fechas
        if not start_date or not end_date:
            return Response({"error": "Se deben proporcionar las fechas de inicio y fin."}, status=400)

        try:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
        except ValueError:
            return Response({"error": "Las fechas deben estar en formato ISO."}, status=400)

        # Verificar que el grupo existe y que el usuario pertenece al grupo
        try:
            group = Group.objects.get(id=group_id)
            membership = GroupMembership.objects.filter(group=group, user=request.user)
            if not membership.exists():
                return Response({"error": "No perteneces a este grupo."}, status=403)
        except Group.DoesNotExist:
            return Response({"error": "El grupo especificado no existe."}, status=404)

        # Obtener todos los miembros del grupo
        group_members = GroupMembership.objects.filter(group=group).values_list('user', flat=True)

        # Obtener eventos de todos los miembros en el rango de fechas
        events = Event.objects.filter(
            participants__in=group_members,
            start_time__gte=start_date,
            end_time__lte=end_date
        ).distinct()

        # Construir la respuesta basada en la privacidad
        timeline = []
        for event in events:
            for participant in event.participants.all():
                member_name = participant.username  # Nombre del miembro

                if request.user == participant:
                    # Si el usuario es participante, mostrar detalles completos
                    timeline.append({
                        "id": event.id,
                        "title": event.title,
                        "description": event.description,
                        "start_time": event.start_time,
                        "end_time": event.end_time,
                        "organizer": event.organizer.username,
                        "member": member_name,  # Mostrar nombre del miembro
                        "status": "detalles completos"
                    })
                else:
                    # Si el usuario no es participante, solo mostrar "ocupado"
                    timeline.append({
                        "id": event.id,
                        "title": "Ocupado",
                        "description": None,
                        "start_time": event.start_time,
                        "end_time": event.end_time,
                        "organizer": None,
                        "member": member_name,  # Mostrar nombre del miembro
                        "status": "ocupado"
                    })

        return Response(timeline)
