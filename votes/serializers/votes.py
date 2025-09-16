import os
import logging
from binascii import hexlify
from hashlib import sha256
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from rest_framework import serializers
from web3.exceptions import ContractLogicError
from accounts.models import GENDER_CHOICES
from votes.models import Vote
from elections.models.candidates import Candidate

logger = logging.getLogger(__name__)


class AnonymousVoteSerializer(serializers.ModelSerializer):
    candidate_code = serializers.CharField(write_only=True)
    position_code = serializers.CharField(write_only=True)
    election_code = serializers.CharField(write_only=True)
    is_synced = serializers.BooleanField(read_only=True)

    class Meta:
        model = Vote
        fields = [
            "candidate_code", "position_code", "election_code",
            "timestamp", "receipt", "tx_hash", "is_synced",
            "block_number", "network_fee_matic","block_confirmations", "block_timestamp", "status"
        ]
        read_only_fields = [
            "timestamp", "receipt", "tx_hash", "is_synced","network_fee_matic",
            "block_number", "block_confirmations", "block_timestamp", "status"
        ]

    def validate(self, data):
        user = self.context["request"].user
        did = user.did
        if not did:
            raise serializers.ValidationError("User DID not found.")

        did_hash = sha256(did.encode()).hexdigest()

        try:
            candidate = Candidate.objects.select_related("position__election", "student").get(
                code=data["candidate_code"]
            )
        except Candidate.DoesNotExist:
            raise serializers.ValidationError("Invalid candidate code.")

        position = candidate.position
        election = position.election

        # Integrity checks
        if data["position_code"] != position.code:
            raise serializers.ValidationError("Position code mismatch.")
        if data["election_code"] != election.code:
            raise serializers.ValidationError("Election code mismatch.")
        if user.current_level == 4:
            raise serializers.ValidationError("Level 400 students are not allowed to vote.")
        if not position.is_user_eligible(user):
            raise serializers.ValidationError("You are not eligible to vote for this position.")
        if not election.has_started():
            raise serializers.ValidationError("Election has not started yet.")
        if election.has_ended():
            raise serializers.ValidationError("Election has already ended.")
        if Vote.objects.filter(voter_did_hash=did_hash, position=position).exists():
            raise serializers.ValidationError("You have already voted for this position.")

        if position.gender and position.gender != "A":
            if not user.gender or user.gender.lower() != position.gender.lower():
                raise serializers.ValidationError(
                    f"This position is restricted to {dict(GENDER_CHOICES).get(position.gender)} voters only."
                )

        # Attach resolved objects
        data["voter_did_hash"] = did_hash
        data["position"] = position
        data["election"] = election
        data["candidate"] = candidate
        return data

    def create(self, validated_data):
        from blockchain.helpers import cast_vote
        from blockchain.utils import web3

        voter_did_hash = validated_data["voter_did_hash"]
        candidate = validated_data["candidate"]
        position = validated_data["position"]
        election = validated_data["election"]

        # Generate ONE receipt tied to THIS candidate only
        receipt_hash_hex = hexlify(os.urandom(32)).decode()

        try:
            tx_receipt = cast_vote(position.code, candidate.code, receipt_hash_hex)
            tx_hash = tx_receipt["transactionHash"].hex()

            # Persist vote immediately
            with transaction.atomic():
                vote = Vote.objects.create(
                    candidate=candidate,
                    position=position,
                    election=election,
                    voter_did_hash=voter_did_hash,
                    receipt=receipt_hash_hex,
                    tx_hash=tx_hash,
                    status="Pending",
                    is_synced=True,
                )

            # Best-effort update with blockchain info
            try:
                block_number = tx_receipt.get("blockNumber")
                confirmations, block_timestamp, fee_matic = None, None, None
                status = "Success" if tx_receipt.get("status") == 1 else "Failed"

                if block_number:
                    block = web3.eth.get_block(block_number)
                    latest_block = web3.eth.block_number
                    confirmations = latest_block - block_number
                    if isinstance(block.timestamp, (int, float)):
                        block_timestamp = timezone.make_aware(datetime.fromtimestamp(block.timestamp))

                # compute transaction fee directly from receipt
                gas_used = tx_receipt.get("gasUsed")
                gas_price = tx_receipt.get("effectiveGasPrice") or tx_receipt.get("gasPrice")
                if gas_used and gas_price:
                    fee_matic = web3.from_wei(gas_used * gas_price, "ether")

                vote.block_number = block_number
                vote.block_confirmations = confirmations
                vote.block_timestamp = block_timestamp
                vote.status = status
                if fee_matic is not None:
                    vote.network_fee_matic = str(fee_matic)  # store as string or Decimal depending on model
                vote.save(update_fields=[
                    "block_number", "block_confirmations", "block_timestamp",
                    "status", "network_fee_matic"
                ])
            except Exception as e:
                logger.warning(f"Block info update failed after single vote: {e}")

            return vote

        except ContractLogicError as e:
                if "Receipt already used" in str(e):
                    raise serializers.ValidationError("Blockchain reports duplicate receipt.")
                raise
        except Exception as e:
                logger.exception(f"Unexpected error while casting single vote: {e}")
                raise serializers.ValidationError("Voting failed unexpectedly.")
