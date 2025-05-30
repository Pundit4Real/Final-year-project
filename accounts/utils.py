from eth_account import Account
import secrets

def generate_did():
    acct = Account.create(secrets.token_hex(32))
    return acct.address, f"did:ethr:{acct.address}", acct.key.hex()
