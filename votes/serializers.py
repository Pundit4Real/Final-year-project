from rest_framework import serializers
from votes.models import Vote
from elections.models.candidates import Candidate
from hashlib import sha256
import logging
from django.db import transaction
from web3.exceptions import ContractLogicError

logger = logging.getLogger(__name__)

class AnonymousVoteSerializer(serializers.ModelSerializer):
    candidate_code = serializers.CharField(write_only=True)
    position_code = serializers.CharField(write_only=True)
    election_code = serializers.CharField(write_only=True)
    is_synced = serializers.BooleanField(read_only=True)  # New field added

    class Meta:
        model = Vote
        fields = [
            'candidate_code', 'position_code', 'election_code',
            'timestamp', 'receipt', 'tx_hash', 'is_synced'
        ]
        read_only_fields = ['timestamp', 'receipt', 'tx_hash', 'is_synced']

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

        # Attach the resolved objects
        data['voter_did_hash'] = did_hash
        data['position'] = position
        data['election'] = election
        data['candidate'] = candidate
        return data
        
    def create(self, validated_data):
        from blockchain.helpers import cast_vote
        from blockchain.utils import generate_receipt_hash
        from web3 import Web3

        validated_data.pop('candidate_code', None)
        validated_data.pop('position_code', None)
        validated_data.pop('election_code', None)

        candidate = validated_data['candidate']
        position = validated_data['position']
        election = validated_data['election']
        voter_did_hash = validated_data['voter_did_hash']

        receipt_hash = generate_receipt_hash(voter_did_hash)
        receipt_hash_hex = Web3.to_hex(receipt_hash)

        try:
            with transaction.atomic():
                # Double check no duplicate vote before blockchain call
                if Vote.objects.filter(voter_did_hash=voter_did_hash, position=position).exists():
                    raise serializers.ValidationError("You have already voted for this position.")

                # Cast vote on blockchain
                tx_receipt = cast_vote(position.code, candidate.code, receipt_hash_hex)
                tx_hash = tx_receipt['transactionHash'].hex()

                # Save vote record locally only after blockchain success
                vote = Vote.objects.create(
                    candidate=candidate,
                    position=position,
                    election=election,
                    voter_did_hash=voter_did_hash,
                    receipt=receipt_hash_hex,
                    tx_hash=tx_hash,
                    is_synced=True
                )
            return vote

        except ContractLogicError as e:
            if 'Receipt already used' in str(e):
                raise serializers.ValidationError("You have already voted for this position (on blockchain).")
            logger.exception("Blockchain vote contract logic error")
            raise serializers.ValidationError("Blockchain vote failed due to contract error.")
        except serializers.ValidationError:
            raise
        except Exception as e:
            logger.exception("Unexpected error during voting")
            raise serializers.ValidationError("Voting failed due to an unexpected error.")
