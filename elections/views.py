from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from elections.models import Election
from elections.serializers import ElectionSerializer, ElectionDetailSerializer
from django.db.models import Q
from elections.serializers import PositionSerializer, CandidateSerializer
from rest_framework.generics import RetrieveAPIView
from django.shortcuts import get_object_or_404
from elections.models import Position, Candidate


class ElectionListView(generics.ListAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Election.objects.filter(
            Q(department__isnull=True) | Q(department=user.department)
        )


class ElectionDetailView(generics.RetrieveAPIView):
    serializer_class = ElectionDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'code'

    def get_queryset(self):
        user = self.request.user
        return Election.objects.filter(
            Q(department__isnull=True) | Q(department=user.department)
        ).prefetch_related('positions__candidates')

    def retrieve(self, request, *args, **kwargs):
        election = self.get_object()
        if not election.has_started():
            return Response(
                {"detail": "This election has not started yet. You can only view information."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().retrieve(request, *args, **kwargs)

class PositionDetailView(RetrieveAPIView):
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        code = self.kwargs.get('code')
        return get_object_or_404(Position, code=code)


class CandidateDetailView(RetrieveAPIView):
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        code = self.kwargs.get('code')
        return get_object_or_404(Candidate, code=code)