from django.db.models import Q, Count
from django.db import models
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from elections.filters import ElectionFilter
from elections.models.elections import Election
from elections.serializers.elections import ElectionSerializer, ElectionDetailSerializer


class BaseElectionView:
    """Mixin to set serializer context and filter elections by user department/school."""
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        user = self.request.user
        department = getattr(user, "department", None)
        school = getattr(department, "school", None) if department else None

        return Election.objects.filter(
            Q(department__isnull=True, school__isnull=True) |
            Q(department=department) |
            Q(school=school)
        ).annotate(
            total_candidates=Count('positions__candidates', distinct=True),
            total_positions=Count('positions', distinct=True)
        ).select_related('department', 'school') \
         .order_by('-created_at') 


class ElectionListView(BaseElectionView, generics.ListAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = ElectionFilter



class ElectionSummaryView(generics.GenericAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        department = getattr(user, "department", None)
        school = getattr(department, "school", None) if department else None

        # Custom status ranking
        status_order = {
            "ongoing": 1,
            "upcoming": 2,
            "postponed": 3,
            "ended": 4,
            "draft": 5,
            "cancelled": 6,
        }

        queryset = Election.objects.filter(
            Q(department__isnull=True, school__isnull=True) |
            Q(department=department) |
            Q(school=school)
        ).annotate(
            status_rank=models.Case(
                *[models.When(status=k, then=models.Value(v)) for k, v in status_order.items()],
                default=models.Value(99),
                output_field=models.IntegerField(),
            )
        ).order_by("status_rank", "-created_at")

        return queryset

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        summary = qs.aggregate(
            upcoming=Count('id', filter=Q(status=Election.Status.UPCOMING)),
            ongoing=Count('id', filter=Q(status=Election.Status.ONGOING)),
            ended=Count('id', filter=Q(status=Election.Status.ENDED)),
            postponed=Count('id', filter=Q(status=Election.Status.POSTPONED)),
            cancelled=Count('id', filter=Q(status=Election.Status.CANCELLED)),
            total=Count('id')
        )
        return Response(summary)


class ElectionDetailView(BaseElectionView, generics.RetrieveAPIView):
    serializer_class = ElectionDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'code'

    def get_queryset(self):
        return super().get_queryset().prefetch_related('positions__candidates')

    def retrieve(self, request, *args, **kwargs):
        election = self.get_object()
        data = self.get_serializer(election).data

        # ✅ Filter positions using Position.is_user_eligible
        user = request.user
        filtered_positions = []
        for pos in election.positions.all():
            if pos.is_user_eligible(user):
                # Keep only eligible positions in serialized response
                for serialized in data.get("positions", []):
                    if serialized["code"] == pos.code:
                        filtered_positions.append(serialized)
                        break
        data["positions"] = filtered_positions

        # ✅ Notices based on election status
        if election.status == election.Status.UPCOMING:
            data["notice"] = "This election has not started yet. You can only view information."
        elif election.status == election.Status.ENDED:
            data["notice"] = "This election has ended. You can only view past results."
        else:
            data["notice"] = (
                "You have already voted in this election." if data.get("has_voted")
                else "Voting is currently open."
            )

        return Response(data)
