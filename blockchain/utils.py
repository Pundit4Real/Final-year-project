# blockchain/utils.py
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from dotenv import load_dotenv
import os
import json
import hashlib
from eth_account import Account

load_dotenv()

INFURA_URL = os.getenv("INFURA_URL")
PRIVATE_KEY = os.getenv("PK")
WALLET_ADDRESS = os.getenv("WA")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

web3 = Web3(Web3.HTTPProvider(INFURA_URL))
web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

assert web3.is_connected(), "❌ Failed to connect to Polygon Amoy"

# Load ABI only (compiled contract no longer needed post-deployment)
with open("blockchain/abi.json") as f:  
    abi = json.load(f)

def contract():
    return web3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

def build_and_send_tx(fn, *args):
    acct = web3.eth.account.from_key(PRIVATE_KEY)
    tx = fn(*args).build_transaction({
        'from': acct.address,
        'nonce': web3.eth.get_transaction_count(acct.address),
        'gas': 300000,
        'gasPrice': web3.to_wei('26', 'gwei')
    })
    signed_txn = acct.sign_transaction(tx)

    # ✅ Fix: Use correct attribute based on sign result
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    return web3.eth.wait_for_transaction_receipt(tx_hash)


def generate_receipt_hash(did: str) -> bytes:
    return web3.keccak(text=did)

