from eth_account import Account
import secrets
from django.db.models import Max
import re
from datetime import datetime

SCHOOL_PREFIX = "SO"


def generate_did():
    acct = Account.create(secrets.token_hex(32))
    return acct.address, f"did:ethr:{acct.address}", acct.key.hex()


def short_code(name, length=3):
    """
    Generate a fixed-length uppercase code from a name by:
    - Removing non-alpha chars
    - Taking the first `length` letters directly
    - Padding with 'X' if too short
    """
    if not name:
        return "X" * length
    cleaned = re.sub(r'[^A-Za-z]', '', name).upper()
    return (cleaned[:length]).ljust(length, "X")


def expand_prefix(prefix, length=3):
    """
    Expand prefix to exactly `length` characters by repeating last char if needed.
    """
    cleaned = re.sub(r'[^A-Za-z]', '', prefix).upper()
    return (cleaned + cleaned[-1] * (length - len(cleaned)))[:length]


def generate_code(prefix, department_name=None, school_name=None, scope=None, seq_length=3):
    """
    Generates a unique election/position/candidate code with structure:
    PREFIX - SCOPE - UNIT - YEAR + SEQ
    - PREFIX: e.g. EL, POS, CND (unchanged)
    - SCOPE: SCH (school), DPT (department), or UNI/other
    - UNIT: For school -> SCHOOL_PREFIX + 3-letter school code (e.g. SOSCI)
            For department -> 3-letter dept code
            For others -> 'GEN'
    - YEAR + SEQ: e.g. 25001 for 2025, seq 001

    The sequence resets each year per scope/unit and increments until unique.
    seq_length controls the zero-padded length of the sequence number.
    """

    from elections.models.elections import Election
    from elections.models.candidates import Candidate
    from elections.models.positions import Position

    prefix = prefix.upper()
    model_map = {
        "EL": Election,
        "POS": Position,
        "CND": Candidate,
    }

    Model = model_map.get(prefix)
    if not Model:
        raise ValueError(f"Unsupported prefix for code generation: {prefix}")

    current_year = datetime.now().year
    year_part = datetime.now().strftime("%y")

    if school_name:
        scope_part = "SCH"
        cleaned_school = school_name.upper()
        cleaned_school = re.sub(r'^SCHOOL OF\s+', '', cleaned_school)
        cleaned_school = re.sub(r'^SCHOOL\s+', '', cleaned_school)
        # First 3 letters directly, padded if needed
        school_short = cleaned_school[:3].ljust(3, "X")
        unit_part = SCHOOL_PREFIX + school_short  # e.g. SO + SCI

    elif department_name:
        scope_part = "DPT"
        # First 3 letters directly, padded if needed
        unit_part = department_name.upper()[:3].ljust(3, "X")

    else:
        scope_part = short_code(scope or "UNI", 3)
        unit_part = "GEN"

    # Build filter for latest code by scope/unit/year
    unit_filter = {}
    if prefix == "CND":
        if school_name:
            unit_filter["position__election__school__name__iexact"] = school_name
        elif department_name:
            unit_filter["position__election__department__name__iexact"] = department_name
    elif prefix == "POS":
        if school_name:
            unit_filter["election__school__name__iexact"] = school_name
        elif department_name:
            unit_filter["election__department__name__iexact"] = department_name
    else:  # EL or others
        if school_name:
            unit_filter["school__name__iexact"] = school_name
        elif department_name:
            unit_filter["department__name__iexact"] = department_name

    latest_code = (
        Model.objects.filter(
            created_at__year=current_year,
            **unit_filter
        )
        .aggregate(Max("code"))["code__max"]
    )

    if latest_code:
        match = re.search(r"(\d{%d})$" % seq_length, latest_code)
        last_seq = int(match.group(1)) if match else 0
    else:
        last_seq = 0

    next_seq = last_seq + 1
    max_seq = 10 ** seq_length - 1

    while next_seq <= max_seq:
        number_part = str(next_seq).zfill(seq_length)
        code = f"{prefix}-{scope_part}-{unit_part}-{year_part}{number_part}"

        if not Model.objects.filter(code=code).exists():
            return code
        next_seq += 1

    raise ValueError(f"Code generation failed: exhausted sequence numbers up to {max_seq}")
