from django.urls import path
from votes.views import CastVoteView, VoteVerificationView

urlpatterns = [
    path('cast/', CastVoteView.as_view(), name='cast-vote'),
    path('verify/', VoteVerificationView.as_view(), name='verify-vote'),
]
