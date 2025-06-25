from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to the Polygon network
web3 = Web3(Web3.HTTPProvider(os.getenv("INFURA_URL")))

# Confirm connection
if web3.is_connected():
    print("✅ Connected to Polygon Amoy Testnet")
else:
    print("❌ Failed to connect to Polygon Amoy")


# Replace with your wallet address
wallet_address = os.getenv("WA")

# Get and print MATIC balance
if web3.is_address(wallet_address):
    balance = web3.eth.get_balance(wallet_address)
    print("Balance (MATIC):", web3.from_wei(balance, 'ether'))
else:
    print("⚠️ Invalid wallet address")
