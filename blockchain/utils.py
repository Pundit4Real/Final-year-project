# blockchain/utils.py

import os
import json
import binascii
from web3 import Web3
from web3.exceptions import TimeExhausted, ContractLogicError
from dotenv import load_dotenv
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware

from blockchain.web3_config import web3, check_connection
from elections.models.positions import Position
from elections.models.candidates import Candidate
from elections.models.elections import Election

load_dotenv()

PRIVATE_KEY = os.getenv("PK")
WALLET_ADDRESS = os.getenv("WA")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
CHAIN_ID = int(os.getenv("CHAIN_ID", 137))

# ---------------------- Inject POA Middleware globally ----------------------
MW_NAME = "ExtraDataToPOAMiddleware"
existing_mws = [mw.__class__.__name__ for mw in web3.middleware_onion]

if MW_NAME not in existing_mws:
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0, name=MW_NAME)
else:
    idx = existing_mws.index(MW_NAME)
    web3.middleware_onion.replace(idx, ExtraDataToPOAMiddleware(), name=MW_NAME)

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
def to_bytes32(val):
    """Convert string/hex/bytes to bytes32, auto-detecting hex strings."""
    if val is None:
        raise ValueError("Cannot convert None to bytes32")

    if isinstance(val, bytes):
        if len(val) > 32:
            raise ValueError(f"Value too long for bytes32: {val!r} ({len(val)} bytes)")
        return val.ljust(32, b"\0")

    if isinstance(val, str):
        s = val.strip()
        hex_candidate = s[2:] if s.startswith("0x") else s
        try:
            raw_bytes = binascii.unhexlify(hex_candidate)
            if len(raw_bytes) <= 32:
                return raw_bytes.ljust(32, b"\0")
            else:
                raise ValueError(f"Value too long for bytes32 after hex decoding: {val!r} ({len(raw_bytes)} bytes)")
        except binascii.Error:
            encoded = s.encode("utf-8")
            if len(encoded) > 32:
                raise ValueError(f"Value too long for bytes32: {val!r} ({len(encoded)} bytes)")
            return encoded.ljust(32, b"\0")

    s = str(val)
    encoded = s.encode("utf-8")
    if len(encoded) > 32:
        raise ValueError(f"Value too long for bytes32: {val!r} ({len(encoded)} bytes)")
    return encoded.ljust(32, b"\0")


def from_bytes32(value):
    return value.rstrip(b'\0').decode('utf-8')


# ---------------------- Hash Helpers ----------------------
def generate_receipt_hash(did: str, as_hex: bool = False):
    check_connection()
    if not did or not isinstance(did, str):
        raise ValueError("DID must be a non-empty string.")
    hash_bytes = Web3.keccak(text=did)
    return hash_bytes.hex() if as_hex else hash_bytes


# ---------------------- Revert Reason Extractor ----------------------
def extract_revert_reason(tx_dict):
    """
    Try to extract the revert reason by simulating a call with the same tx.
    """
    try:
        web3.eth.call({
            "from": tx_dict.get("from"),
            "to": tx_dict.get("to"),
            "data": tx_dict.get("data"),
        }, "latest")
    except ContractLogicError as e:
        msg = str(e)
        if "execution reverted" in msg:
            return msg.replace("execution reverted: ", "")
        return msg
    except Exception as e:
        return str(e)
    return None


# ---------------------- Transaction Builder ----------------------
def build_and_send_tx(fn, *args):
    check_connection()
    acct = web3.eth.account.from_key(PRIVATE_KEY)
    if acct.address.lower() != WALLET_ADDRESS.lower():
        raise ValueError("Wallet address mismatch")

    nonce = web3.eth.get_transaction_count(acct.address, 'pending')

    # --- Estimate gas with clean revert reason ---
    try:
        gas_estimate = fn(*args).estimate_gas({'from': acct.address})
        print(f"🧪 Gas estimate: {gas_estimate}")
    except ContractLogicError as e:
        raise Exception(f"⛔ Contract revert: {str(e)}")
    except Exception as e:
        raise Exception(f"⚠️ Gas estimation failed: {e}")

    tx = fn(*args).build_transaction({
        'from': acct.address,
        'nonce': nonce,
        'gas': int(gas_estimate * 1.2),
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
        reason = extract_revert_reason(tx)
        raise Exception(f"⏳ TX not mined in time: {tx_hash.hex()} | Reason: {reason or 'Unknown'}")


# ---------------------- Election/Position/Candidate Actions ----------------------
# ---------------------- Queries (local helpers) ----------------------
def _position_exists_onchain(position_code: str) -> bool:
    return contract().functions.positionExists(to_bytes32(position_code)).call()

def _election_exists_onchain(election_code: str) -> bool:
    return contract().functions.electionExists(to_bytes32(election_code)).call()

def _candidate_exists_onchain(position_code: str, candidate_code: str) -> bool:
    # uses the contract helper for O(1) lookup instead of scanning results
    return contract().functions.candidateExists(
        to_bytes32(position_code), to_bytes32(candidate_code)
    ).call()

# ---------------------- Election/Position/Candidate Actions ----------------------
def add_position(position_code, title, election_code, mark_synced=True):
    # idempotency guard
    if not _election_exists_onchain(election_code):
        raise ValueError(f"Election {election_code} does not exist on-chain.")
    if _position_exists_onchain(position_code):
        if mark_synced:
            Position.objects.filter(code=position_code).update(is_synced=True)
        return None  # already exists, nothing to do

    receipt = build_and_send_tx(
        contract().functions.addPosition,
        to_bytes32(position_code), title, to_bytes32(election_code)
    )
    if mark_synced:
        Position.objects.filter(code=position_code).update(is_synced=True)
    return receipt

def add_candidate(position_code, candidate_code, name, mark_synced=True):
    # idempotency guard
    if not _position_exists_onchain(position_code):
        raise ValueError(f"Position {position_code} does not exist on-chain.")
    if _candidate_exists_onchain(position_code, candidate_code):
        if mark_synced:
            Candidate.objects.filter(code=candidate_code).update(is_synced=True)
        return None  # already exists, nothing to do

    receipt = build_and_send_tx(
        contract().functions.addCandidate,
        to_bytes32(position_code), to_bytes32(candidate_code), name
    )
    if mark_synced:
        Candidate.objects.filter(code=candidate_code).update(is_synced=True)
    return receipt

# ---------------------- Sync Flow ----------------------
def sync_election(election):
    """
    Idempotent sync:
      - Ensures election exists on-chain (no-op if present)
      - Adds missing positions/candidates only once
    Safe to call repeatedly without spamming transactions.
    """
    # normalize inputs
    if not isinstance(election, str):
        election_code = election.code
    else:
        election_code = election
        election = Election.objects.get(code=election_code)

    # ensure election on-chain (no-op if already there)
    if not _election_exists_onchain(election_code):
        build_and_send_tx(contract().functions.addElection, to_bytes32(election_code))
        Election.objects.filter(code=election_code).update(is_synced=True)

    # light runaway guard (prevent accidental unbounded loops in callers)
    tx_count = 0
    TX_CAP = 200  # plenty, but prevents accidental firehose

    # positions
    for position in Position.objects.filter(election=election):
        if not _position_exists_onchain(position.code):
            add_position(position.code, position.title, election_code)
            tx_count += 1
            if tx_count >= TX_CAP:
                break
        else:
            Position.objects.filter(code=position.code).update(is_synced=True)

        # candidates
        for candidate in Candidate.objects.filter(position=position):
            if not _candidate_exists_onchain(position.code, candidate.code):
                add_candidate(position.code, candidate.code, candidate.student.full_name)
                tx_count += 1
                if tx_count >= TX_CAP:
                    break
            else:
                Candidate.objects.filter(code=candidate.code).update(is_synced=True)