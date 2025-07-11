# blockchain/utils.py
from web3 import Web3
from dotenv import load_dotenv
import os
import json
from web3.exceptions import TimeExhausted

load_dotenv()

ALCHEMY_URL = os.getenv("ALCHEMY_URL")
PRIVATE_KEY = os.getenv("PK")
WALLET_ADDRESS = os.getenv("WA")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
CHAIN_ID = int(os.getenv("CHAIN_ID", 137))

web3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

assert web3.is_connected(), "❌ Failed to connect to Polygon Mainnet via Alchemy"

# Load ABI
with open("blockchain/abi.json") as f:
    abi = json.load(f)

def contract():
    return web3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

def build_and_send_tx(fn, *args):
    acct = web3.eth.account.from_key(PRIVATE_KEY)
    assert acct.address.lower() == WALLET_ADDRESS.lower(), "❗ Wallet address mismatch"

    nonce = web3.eth.get_transaction_count(acct.address, 'pending')

    try:
        estimated_gas = fn(*args).estimate_gas({'from': acct.address})
        print("🧪 Estimated Gas:", estimated_gas)
    except Exception as e:
        print("❌ Gas estimation failed:", str(e))
        raise Exception("Smart contract call may revert. Check arguments or contract logic.")

    gas_price = int(web3.eth.gas_price * 1.4)
    gas_limit = 300000  # You can adjust this if your contract's functions require more.

    tx = fn(*args).build_transaction({
        'from': acct.address,
        'nonce': nonce,
        'gas': gas_limit,
        'gasPrice': gas_price,
        'chainId': CHAIN_ID
    })

    signed_tx = acct.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_hash_hex = tx_hash.hex()

    print(f"📦 TX Hash: {tx_hash_hex}")
    try:
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60, poll_latency=5)
        print("✅ Transaction mined:", receipt.transactionHash.hex())
        return receipt
    except TimeExhausted:
        print(f"⏳ Timeout: TX not mined after waiting — {tx_hash_hex}")
        raise Exception("Transaction took too long to be mined.")

def generate_receipt_hash(did: str) -> bytes:
    return web3.keccak(text=did)
