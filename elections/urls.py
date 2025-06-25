from django.urls import path
from .views import (
    ElectionListView, ElectionDetailView,
    PositionDetailView, CandidateDetailView,
    PositionCreateView, CandidateCreateView
)

urlpatterns = [
    path('elections/', ElectionListView.as_view(), name='election-list'),
    path('elections/<str:code>/', ElectionDetailView.as_view(), name='election-detail'),
    path('positions/<str:code>/', PositionDetailView.as_view(), name='position-detail'),
    path('candidates/<str:code>/', CandidateDetailView.as_view(), name='candidate-detail'),
    path('positions/create/', PositionCreateView.as_view(), name='position-create'),
    path('candidates/create/', CandidateCreateView.as_view(), name='candidate-create'),
]
