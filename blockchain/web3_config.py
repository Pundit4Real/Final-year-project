from web3 import Web3

# Polygon Amoy Testnet Infura URL
INFURA_URL = "https://polygon-amoy.infura.io/v3/aadf3e661b4f4d2783ed8b7ba2ee555a"

# Connect to the Polygon network
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Confirm connection
if web3.is_connected():
    print("✅ Connected to Polygon Amoy Testnet")
else:
    print("❌ Failed to connect to Polygon Amoy")


# Replace with your wallet address
wallet_address = "0x1d8ce29d5452544E9656E4c99bC3765bB61653A1"

# Get and print MATIC balance
if web3.is_address(wallet_address):
    balance = web3.eth.get_balance(wallet_address)
    print("Balance (MATIC):", web3.from_wei(balance, 'ether'))
else:
    print("⚠️ Invalid wallet address")
