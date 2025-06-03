from django.urls import path
from .views import ElectionListView, ElectionDetailView

urlpatterns = [
    path('elections/', ElectionListView.as_view(), name='election-list'),
    path('elections/<int:pk>/', ElectionDetailView.as_view(), name='election-detail'),
]
