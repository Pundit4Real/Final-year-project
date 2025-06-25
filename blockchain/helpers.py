# blockchain/helper.py
from .utils import contract, build_and_send_tx

def add_position(position_code, title, election_code):
    return build_and_send_tx(contract().functions.addPosition, position_code, title, election_code)

def add_candidate(position_code, candidate_code, name):
    return build_and_send_tx(contract().functions.addCandidate, position_code, candidate_code, name)

def cast_vote(position_code, candidate_code, receipt_hash):
    return build_and_send_tx(contract().functions.vote, position_code, candidate_code, receipt_hash)

def get_results(position_code):
    return contract().functions.getResults(position_code).call()
