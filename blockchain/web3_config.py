# blockchain/web3_config.py
from web3 import Web3
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Use Alchemy as provider
ALCHEMY_URL = os.getenv("ALCHEMY_URL")
web3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))


def check_connection():
    """Ensure web3 is connected to the blockchain."""
    if not web3.is_connected():
        raise ConnectionError("❌ Not connected to Polygon Mainnet — check your RPC URL and network status")
    return True


# Confirm connection on startup
if web3.is_connected():
    print("✅ Connected to Polygon Mainnet via Alchemy")
    print(f"ℹ️ Node Info: {web3.client_version}")
    print(f"⛓️ Latest Block: {web3.eth.block_number}")
else:
    print("❌ Failed to connect to Polygon Mainnet")

# Wallet balance check
wallet_address = os.getenv("WA")
if web3.is_address(wallet_address):
    balance = web3.eth.get_balance(wallet_address)
    print("💰 Wallet Balance (MATIC):", web3.from_wei(balance, 'ether'))
else:
    print("⚠️ Invalid wallet address in .env file")
