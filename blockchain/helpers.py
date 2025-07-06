# blockchain/helpers.py
from .utils import contract, build_and_send_tx
from elections.models import Position, Candidate
from .utils import build_and_send_tx, contract

def add_position(position_code, title, election_code):
    return build_and_send_tx(
        contract().functions.addPosition,
        position_code, title, election_code
    )

def add_candidate(position_code, candidate_code, name):
    return build_and_send_tx(
        contract().functions.addCandidate,
        position_code, candidate_code, name
    )

def cast_vote(position_code, candidate_code, receipt_hash_hex):
    return build_and_send_tx(
        contract().functions.vote,
        position_code, candidate_code, receipt_hash_hex
    )

def get_results(position_code):
    return contract().functions.getResults(position_code).call()

def sync_election(election):
    for position in Position.objects.filter(election=election):
        build_and_send_tx(contract().functions.addPosition, position.code, position.title, election.code)
        for candidate in Candidate.objects.filter(position=position):
            build_and_send_tx(contract().functions.addCandidate, position.code, candidate.code, candidate.student.full_name)
