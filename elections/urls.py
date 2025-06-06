from django.urls import path
from elections.views import ElectionListView, ElectionDetailView, PositionDetailView, CandidateDetailView

urlpatterns = [
    path('elections/', ElectionListView.as_view(), name='election-list'),
    path('elections/<str:code>/', ElectionDetailView.as_view(), name='election-detail'),
    path('positions/<str:code>/', PositionDetailView.as_view(), name='position-detail'),
    path('candidates/<str:code>/', CandidateDetailView.as_view(), name='candidate-detail'),
]
