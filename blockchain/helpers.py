from .utils import contract, build_and_send_tx
from elections.models import Position, Candidate

def add_position(position_code, title, election_code, mark_synced=True):
    receipt = build_and_send_tx(
        contract().functions.addPosition,
        position_code, title, election_code
    )
    if mark_synced:
        Position.objects.filter(code=position_code).update(is_synced=True)
    return receipt

def add_candidate(position_code, candidate_code, name, mark_synced=True):
    receipt = build_and_send_tx(
        contract().functions.addCandidate,
        position_code, candidate_code, name
    )
    if mark_synced:
        Candidate.objects.filter(code=candidate_code).update(is_synced=True)
    return receipt

def cast_vote(position_code, candidate_code, receipt_hash_hex):
    return build_and_send_tx(
        contract().functions.vote,
        position_code, candidate_code, receipt_hash_hex
    )

def get_results(position_code):
    return contract().functions.getResults(position_code).call()

def sync_election(election):
    # Still available for legacy use, though now we prefer syncing via Position & Candidate
    for position in Position.objects.filter(election=election):
        add_position(position.code, position.title, election.code)
        for candidate in Candidate.objects.filter(position=position):
            add_candidate(position.code, candidate.code, candidate.student.full_name)
