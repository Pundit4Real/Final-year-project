from web3 import Web3

web3 = Web3(Web3.HTTPProvider("https://polygon-amoy.g.alchemy.com/v2/e0sQmtHXzhr8BEysKXXGz-A2oVFKZLEa"))

tx_hash = "0xb8828a13054711497dec365655632a0644d5df2a25bbe1a7007f70417b69ba0a"
receipt = web3.eth.get_transaction_receipt(tx_hash)
print(receipt)
tx = web3.eth.get_transaction("0xb8828a13054711497dec365655632a0644d5df2a25bbe1a7007f70417b69ba0a")
print(tx)
