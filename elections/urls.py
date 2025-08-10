from django.urls import path
from elections.views.user_elections import (
    ElectionListView,
    ElectionDetailView,
    ElectionSummaryView
)
from elections.views.admin_elections import (
    AdminElectionCreateView,
    AdminElectionListView,
    AdminElectionSummaryView
)
from elections.views.candidates import (
    CandidateCreateView,
    CandidateDetailView,
    CandidateAdminListView
)
from elections.views.positions import (
    AdminPositionListView,
    PositionCreateView,
    PositionDetailView
)

urlpatterns = [
    # User election endpoints
    path('elections/', ElectionListView.as_view(), name='election-list'),
    path('elections/summary/', ElectionSummaryView.as_view(), name='election-summary'),
    path('elections/<str:code>/', ElectionDetailView.as_view(), name='election-detail'),

    # Admin election endpoints
    path('admin/elections/', AdminElectionListView.as_view(), name='admin-election-list'),
    path('admin/elections/summary/', AdminElectionSummaryView.as_view(), name='admin-election-summary'),
    path('admin/elections/create/', AdminElectionCreateView.as_view(), name='admin-election-create'),

    # Candidates
    path('candidates/<str:code>/', CandidateDetailView.as_view(), name='candidate-detail'),

    # Admin candidates
    path('admin/candidates/create/', CandidateCreateView.as_view(), name='candidate-create'),
    path('admin/candidates/', CandidateAdminListView.as_view(), name='admin-candidate-list'),

    # Positions
        # Admin
    path('admin/positions/', AdminPositionListView.as_view(), name='admin-position-list'),
    path('admin/positions/create/', PositionCreateView.as_view(), name='position-create'),

    # Authenticated user (detail)
    path('positions/<str:code>/', PositionDetailView.as_view(), name='position-detail'),
]
