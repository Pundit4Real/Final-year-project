from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from elections.models.positions import Position
from elections.serializers.positions import PositionSerializer
from blockchain.helpers import add_position


class AdminPositionListView(generics.ListAPIView):
    """
    List all positions (Admin-only).
    """
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class PositionCreateView(generics.CreateAPIView):
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated,IsAdminUser]

    def perform_create(self, serializer):
        position = serializer.save()
        # Push to blockchain
        add_position(position.code, position.title, position.election.code)


class PositionDetailView(generics.RetrieveAPIView):
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        code = self.kwargs.get('code')
        return get_object_or_404(Position, code=code)
