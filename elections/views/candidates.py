from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from elections.models.candidates import Candidate
from elections.serializers.candidates import CandidateSerializer
from blockchain.helpers import add_candidate


class CandidateBaseView:
    """Mixin to ensure request is always in serializer context."""
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class CandidateCreateView(CandidateBaseView, generics.CreateAPIView):
    """
    Admin-only: Create a new candidate.
    Candidate code is auto-generated and pushed to the blockchain.
    """
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def perform_create(self, serializer):
        candidate = serializer.save()
        # Push to blockchain
        add_candidate(
            candidate.position.code,
            candidate.code,
            candidate.student.full_name
        )


class CandidateDetailView(CandidateBaseView, generics.RetrieveAPIView):
    """
    Retrieve details for a specific candidate by code.
    Accessible to authenticated users.
    """
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        code = self.kwargs.get('code')
        return get_object_or_404(Candidate, code=code)


class CandidateAdminListView(CandidateBaseView, generics.ListAPIView):
    """
    Admin-only: List all candidates with related position and student details.
    """
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Candidate.objects.select_related(
            'student', 'position'
        ).order_by('-created_at')

