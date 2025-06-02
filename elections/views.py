from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Election
from .serializers import ElectionSerializer, ElectionDetailSerializer


class ElectionListView(generics.ListAPIView):
    queryset = Election.objects.all()
    serializer_class = ElectionSerializer
    permission_classes = [IsAuthenticated]


class ElectionDetailView(generics.RetrieveAPIView):
    queryset = Election.objects.prefetch_related('positions__candidates').all()
    serializer_class = ElectionDetailSerializer
    permission_classes = [IsAuthenticated]
