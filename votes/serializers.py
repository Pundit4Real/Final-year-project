from rest_framework import serializers
from votes.models import Vote
from elections.models.candidates import Candidate
from hashlib import sha256
import logging
from django.db import transaction
from web3.exceptions import ContractLogicError
import os
from binascii import hexlify
from datetime import datetime

logger = logging.getLogger(__name__)


class AnonymousVoteSerializer(serializers.ModelSerializer):
    candidate_code = serializers.CharField(write_only=True)
    position_code = serializers.CharField(write_only=True)
    election_code = serializers.CharField(write_only=True)
    is_synced = serializers.BooleanField(read_only=True)

    class Meta:
        model = Vote
        fields = [
            'candidate_code', 'position_code', 'election_code',
            'timestamp', 'receipt', 'tx_hash', 'is_synced',
            'block_number', 'block_confirmations', 'block_timestamp', 'status'
        ]
        read_only_fields = [
            'timestamp', 'receipt', 'tx_hash', 'is_synced',
            'block_number', 'block_confirmations', 'block_timestamp', 'status'
        ]

    def validate(self, data):
        user = self.context['request'].user
        did = user.did
        if not did:
            raise serializers.ValidationError("User DID not found.")

        did_hash = sha256(did.encode()).hexdigest()

        try:
            candidate = Candidate.objects.select_related('position__election').get(code=data['candidate_code'])
        except Candidate.DoesNotExist:
            raise serializers.ValidationError("Invalid candidate code.")

        position = candidate.position
        election = position.election

        if data['position_code'] != position.code:
            raise serializers.ValidationError("Position code mismatch.")
        if data['election_code'] != election.code:
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

        # Attach resolved objects
        data['voter_did_hash'] = did_hash
        data['position'] = position
        data['election'] = election
        data['candidate'] = candidate
        return data

    def create(self, validated_data):
        from blockchain.helpers import cast_vote
        from blockchain.utils import web3
        from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware

        # Inject or replace POA middleware safely
        mw_name = "ExtraDataToPOAMiddleware"
        existing_mws = [mw.__class__.__name__ for mw in web3.middleware_onion]

        if mw_name not in existing_mws:
            web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0, name=mw_name)
        else:
            # Replace existing middleware in place
            idx = existing_mws.index(mw_name)
            web3.middleware_onion.replace(idx, ExtraDataToPOAMiddleware(), name=mw_name)


        # Remove write-only codes
        validated_data.pop('candidate_code', None)
        validated_data.pop('position_code', None)
        validated_data.pop('election_code', None)

        candidate = validated_data['candidate']
        position = validated_data['position']
        election = validated_data['election']
        voter_did_hash = validated_data['voter_did_hash']

        # Generate a fresh receipt for every attempt
        receipt_hash_hex = hexlify(os.urandom(32)).decode()

        try:
            with transaction.atomic():
                if Vote.objects.filter(voter_did_hash=voter_did_hash, position=position).exists():
                    raise serializers.ValidationError("You have already voted for this position.")

                # Attempt blockchain vote
                try:
                    tx_receipt = cast_vote(position.code, candidate.code, receipt_hash_hex)
                    tx_hash = tx_receipt['transactionHash'].hex()
                except ContractLogicError as e:
                    if "Receipt already used" in str(e):
                        # User can retry with a new receipt
                        raise serializers.ValidationError(
                            "Blockchain reports that this vote was already cast. Try again with a fresh attempt."
                        )
                    raise

                # Fetch blockchain info safely
                block_number = tx_receipt.get('blockNumber')
                confirmations = None
                block_timestamp = None
                status = "Success" if tx_receipt.get('status') == 1 else "Failed"

                if block_number:
                    try:
                        block = web3.eth.get_block(block_number)
                        latest_block = web3.eth.block_number
                        confirmations = latest_block - block_number
                        if isinstance(block.timestamp, (int, float)):
                            block_timestamp = datetime.fromtimestamp(block.timestamp)
                    except Exception as e:
                        logger.warning(f"Unable to fetch block info for block {block_number}: {e}")

                # Save vote locally
                vote = Vote.objects.create(
                    candidate=candidate,
                    position=position,
                    election=election,
                    voter_did_hash=voter_did_hash,
                    receipt=receipt_hash_hex,
                    tx_hash=tx_hash,
                    is_synced=True,
                    block_number=block_number,
                    block_confirmations=confirmations,
                    block_timestamp=block_timestamp,
                    status=status
                )

            vote.blockchain_info = {
                "status": status,
                "block_number": block_number,
                "block_confirmations": confirmations,
                "block_timestamp": block_timestamp
            }

            return vote

        except serializers.ValidationError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during voting: {e}")
            raise serializers.ValidationError("Voting failed due to an unexpected error.")
