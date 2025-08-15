import os
import json
from web3 import Web3
from web3.exceptions import TimeExhausted
from dotenv import load_dotenv

from blockchain.web3_config import web3, check_connection
from elections.models.positions import Position
from elections.models.candidates import Candidate
from elections.models.elections import Election

load_dotenv()

PRIVATE_KEY = os.getenv("PK")
WALLET_ADDRESS = os.getenv("WA")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
CHAIN_ID = int(os.getenv("CHAIN_ID", 137))

# ---------------------- Load ABI ----------------------
ABI_PATH = os.path.join(os.path.dirname(__file__), "abi.json")
if os.path.exists(ABI_PATH):
    with open(ABI_PATH) as f:
        abi = json.load(f)
else:
    abi = None
    print("⚠️ ABI file not found — contract calls will fail until provided.")


# ---------------------- Contract Instance ----------------------
def contract():
    check_connection()
    if not abi:
        raise FileNotFoundError("ABI not loaded")
    return web3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)


# ---------------------- Bytes32 Helpers ----------------------
import binascii

def to_bytes32(val):
    """Convert string/hex/bytes to bytes32, auto-detecting hex strings."""
    if val is None:
        raise ValueError("Cannot convert None to bytes32")

    # Already bytes
    if isinstance(val, bytes):
        if len(val) > 32:
            raise ValueError(f"Value too long for bytes32: {val!r} ({len(val)} bytes)")
        return val.ljust(32, b"\0")

    if isinstance(val, str):
        s = val.strip()

        # Try interpreting as hex
        hex_candidate = s[2:] if s.startswith("0x") else s
        try:
            raw_bytes = binascii.unhexlify(hex_candidate)
            if len(raw_bytes) <= 32:
                return raw_bytes.ljust(32, b"\0")
            else:
                raise ValueError(f"Value too long for bytes32 after hex decoding: {val!r} ({len(raw_bytes)} bytes)")
        except binascii.Error:
            # Not hex — treat as plain text
            encoded = s.encode("utf-8")
            if len(encoded) > 32:
                raise ValueError(f"Value too long for bytes32: {val!r} ({len(encoded)} bytes)")
            return encoded.ljust(32, b"\0")

    # Fallback for other types
    s = str(val)
    encoded = s.encode("utf-8")
    if len(encoded) > 32:
        raise ValueError(f"Value too long for bytes32: {val!r} ({len(encoded)} bytes)")
    return encoded.ljust(32, b"\0")



def from_bytes32(value):
    return value.rstrip(b'\0').decode('utf-8')



# ---------------------- Hash Helpers ----------------------
def generate_receipt_hash(did: str, as_hex: bool = False):
    """
    Generate a keccak256 hash for the voter's DID.
    Ensures blockchain connection before hashing.
    """
    check_connection()

    if not did or not isinstance(did, str):
        raise ValueError("DID must be a non-empty string.")

    hash_bytes = Web3.keccak(text=did)
    return hash_bytes.hex() if as_hex else hash_bytes


# ---------------------- Transaction Builder ----------------------
def build_and_send_tx(fn, *args):
    check_connection()
    acct = web3.eth.account.from_key(PRIVATE_KEY)
    if acct.address.lower() != WALLET_ADDRESS.lower():
        raise ValueError("Wallet address mismatch")

    nonce = web3.eth.get_transaction_count(acct.address, 'pending')

    try:
        gas_estimate = fn(*args).estimate_gas({'from': acct.address})
        print(f"🧪 Gas estimate: {gas_estimate}")
    except Exception as e:
        raise Exception(f"Gas estimation failed: {e}")

    tx = fn(*args).build_transaction({
        'from': acct.address,
        'nonce': nonce,
        'gas': 300000,
        'gasPrice': int(web3.eth.gas_price * 1.4),
        'chainId': CHAIN_ID
    })

    signed_tx = acct.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print(f"📦 TX Hash: {tx_hash.hex()}")
    try:
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60, poll_latency=5)
        print(f"✅ TX mined: {receipt.transactionHash.hex()}")
        return receipt
    except TimeExhausted:
        raise Exception(f"⏳ TX not mined in time: {tx_hash.hex()}")


# ---------------------- Election/Position/Candidate Actions ----------------------
def add_position(position_code, title, election_code, mark_synced=True):
    receipt = build_and_send_tx(
        contract().functions.addPosition,
        to_bytes32(position_code), title, to_bytes32(election_code)
    )
    if mark_synced:
        Position.objects.filter(code=position_code).update(is_synced=True)
    return receipt


def add_candidate(position_code, candidate_code, name, mark_synced=True):
    receipt = build_and_send_tx(
        contract().functions.addCandidate,
        to_bytes32(position_code), to_bytes32(candidate_code), name
    )
    if mark_synced:
        Candidate.objects.filter(code=candidate_code).update(is_synced=True)
    return receipt


def cast_vote(position_code, candidate_code, receipt_hash):
    return build_and_send_tx(
        contract().functions.vote,
        to_bytes32(position_code), 
        to_bytes32(candidate_code), 
        to_bytes32(receipt_hash)
    )


def get_results(position_code):
    codes, votes = contract().functions.getResults(to_bytes32(position_code)).call()
    return [
        {"candidate_code": from_bytes32(c), "vote_count": v}
        for c, v in zip(codes, votes)
    ]


def sync_election(election):
    if not isinstance(election, str):
        election_code = election.code
    else:
        election_code = election
        election = Election.objects.get(code=election_code)

    for position in Position.objects.filter(election=election):
        if not contract().functions.positionExists(to_bytes32(position.code)).call():
            add_position(position.code, position.title, election_code)

        for candidate in Candidate.objects.filter(position=position):
            if not contract().functions.candidateExists(
                to_bytes32(position.code),
                to_bytes32(candidate.code)
            ).call():
                add_candidate(position.code, candidate.code, candidate.student.full_name)
