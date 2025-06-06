from django.urls import path
from votes.views import CastVoteView, VoteVerificationView, VoteResultsView

urlpatterns = [
    path("cast/", CastVoteView.as_view(), name="cast-vote"),
    path("verify/", VoteVerificationView.as_view(), name="verify-vote"),
    path("results/", VoteResultsView.as_view(), name="vote-results"),
]
