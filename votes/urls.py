from django.urls import path
from votes.views.castvote import CastVoteView
from votes.views.verifyvote import VoteVerificationView
from votes.views.voteresults import VoteResultsView,BlockchainResultsView
from votes.views.votehistory import VoteHistoryView

urlpatterns = [
    path("cast/", CastVoteView.as_view(), name="cast-vote"),
    path("verify/", VoteVerificationView.as_view(), name="verify-vote"),
    path("results/", VoteResultsView.as_view(), name="vote-results"),
    path("results/<str:position_code>/", BlockchainResultsView.as_view(),name="blockchain-results"),
    path("history/",VoteHistoryView.as_view(), name='history')
]
