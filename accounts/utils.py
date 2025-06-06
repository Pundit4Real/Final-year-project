from eth_account import Account
import secrets
from django.db.models import Max

def generate_did():
    acct = Account.create(secrets.token_hex(32))
    return acct.address, f"did:ethr:{acct.address}", acct.key.hex()

def generate_code(prefix, department_name=None, scope=None, length=2):
    from elections.models import Election, Position, Candidate
    model_map = {
        "EL": Election,
        "POS": Position,
        "CND": Candidate,
    }

    Model = model_map.get(prefix)
    if not Model:
        raise ValueError("Unsupported prefix for code generation")

    latest = Model.objects.aggregate(Max("id"))["id__max"] or 0
    new_number = str(latest + 1).zfill(length)

    dept_part = department_name[:2].upper() if department_name else "GN"
    scope_part = scope[:2].upper() if scope else "WD"

    return f"{prefix}-{scope_part}-{dept_part}-{new_number}"
