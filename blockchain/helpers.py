import logging
from .utils import (
    contract,
    build_and_send_tx,
    to_bytes32,
    from_bytes32,
)
from elections.models.elections import Election
from elections.models.positions import Position
from elections.models.candidates import Candidate

logger = logging.getLogger(__name__)

# ----------------------
# Blockchain Add Helpers
# ----------------------

def add_election(election_code, mark_synced=False):
    """
    Add an election on-chain if it doesn't already exist.
    Returns a dict: {status: bool, error: str or None, receipt: object or None}.
    """

    if not election_code:
        return {"status": False, "error": "Election code is required.", "receipt": None}

    try:
        code_bytes = to_bytes32(election_code)

        # Check if already on-chain
        if contract().functions.electionExists(code_bytes).call():
            logger.info(f"Election {election_code} already exists on-chain.")
            if mark_synced:
                Election.objects.filter(code=election_code).update(is_synced=True)
            return {"status": True, "error": None, "receipt": None}

        # Add to blockchain
        receipt = build_and_send_tx(contract().functions.addElection, code_bytes)
        logger.info(f"Election {election_code} deployed to blockchain.")

        if mark_synced:
            Election.objects.filter(code=election_code).update(is_synced=True)

        return {"status": True, "error": None, "receipt": receipt}

    except Exception as e:
        logger.exception(f"Failed to add election {election_code} on-chain.")
        return {"status": False, "error": str(e), "receipt": None}


def add_position(position_code, title, election_code, mark_synced=True):
    """Add a position to an existing election on-chain."""
    election_bytes = to_bytes32(election_code)
    if not contract().functions.electionExists(election_bytes).call():
        raise ValueError(f"Election {election_code} does not exist on-chain.")

    position_bytes = to_bytes32(position_code)
    if position_exists_onchain(position_code):
        logger.info(f"Position {position_code} already exists on-chain.")
        if mark_synced:
            Position.objects.filter(code=position_code).update(is_synced=True)
        return None

    receipt = build_and_send_tx(
        contract().functions.addPosition,
        position_bytes,
        title,
        election_bytes
    )
    logger.info(f"Position {position_code} added to election {election_code}.")

    if mark_synced:
        Position.objects.filter(code=position_code).update(is_synced=True)
    return receipt


def add_candidate(position_code, candidate_code, name, mark_synced=True):
    """Add a candidate to an existing position on-chain."""
    if not position_exists_onchain(position_code):
        raise ValueError(f"Position {position_code} does not exist on-chain.")

    if candidate_exists_onchain(position_code, candidate_code):
        logger.info(f"Candidate {candidate_code} already exists for position {position_code}.")
        if mark_synced:
            Candidate.objects.filter(code=candidate_code).update(is_synced=True)
        return None

    receipt = build_and_send_tx(
        contract().functions.addCandidate,
        to_bytes32(position_code),
        to_bytes32(candidate_code),
        name
    )
    logger.info(f"Candidate {candidate_code} added to position {position_code}.")

    if mark_synced:
        Candidate.objects.filter(code=candidate_code).update(is_synced=True)
    return receipt


# ----------------------
# Blockchain Queries
# ----------------------

def position_exists_onchain(position_code):
    return contract().functions.positionExists(to_bytes32(position_code)).call()


def candidate_exists_onchain(position_code, candidate_code):
    """Check if a candidate exists for a position by scanning results."""
    if not position_exists_onchain(position_code):
        return False
    candidate_codes, _ = get_results(position_code)
    return candidate_code in candidate_codes


def get_results(position_code):
    raw_codes, raw_votes = contract().functions.getResults(to_bytes32(position_code)).call()
    decoded_codes = [from_bytes32(c) for c in raw_codes]
    return decoded_codes, raw_votes


# ----------------------
# Voting
# ----------------------

def cast_vote(position_code, candidate_code, receipt_hash):
    """Cast a vote with validation and flexible receipt hash input."""
    if not position_exists_onchain(position_code):
        raise ValueError(f"Position {position_code} does not exist on-chain.")

    if not candidate_exists_onchain(position_code, candidate_code):
        raise ValueError(f"Candidate {candidate_code} does not exist on-chain.")

    rh_bytes = to_bytes32(receipt_hash)
    return build_and_send_tx(
        contract().functions.vote,
        to_bytes32(position_code),
        to_bytes32(candidate_code),
        rh_bytes
    )


# ----------------------
# Sync Flow
# ----------------------

def sync_election(election_code):
    """Ensure election exists on-chain, then sync positions & candidates."""
    # Step 1: Deploy election if missing
    if not contract().functions.electionExists(to_bytes32(election_code)).call():
        add_election(election_code, mark_synced=True)

    # Step 2: Sync positions
    election = Election.objects.get(code=election_code)
    for position in Position.objects.filter(election=election):
        if not position_exists_onchain(position.code):
            add_position(position.code, position.title, election_code)
        else:
            Position.objects.filter(code=position.code).update(is_synced=True)

        # Step 3: Sync candidates
        for candidate in Candidate.objects.filter(position=position):
            if not candidate_exists_onchain(position.code, candidate.code):
                add_candidate(position.code, candidate.code, candidate.student.full_name)
            else:
                Candidate.objects.filter(code=candidate.code).update(is_synced=True)
