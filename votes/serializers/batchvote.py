import os
import logging
from hashlib import sha256
from binascii import hexlify
from datetime import datetime
from django.db import transaction
from rest_framework import serializers
from votes.models import Vote
from accounts.models import GENDER_CHOICES
from elections.models.candidates import Candidate

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------
# Serializer for full ballot voting (voteBatch)
# -----------------------------------------------------------------
class BallotVoteSerializer(serializers.Serializer):
    election_code = serializers.CharField(write_only=True)
    votes = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        write_only=True
    )

    def validate(self, data):
        user = self.context['request'].user
        did = user.did
        if not did:
            raise serializers.ValidationError("User DID not found.")

        did_hash = sha256(did.encode()).hexdigest()
        election_code = data['election_code']
        validated_votes = []

        for vote_data in data['votes']:
            try:
                candidate = Candidate.objects.select_related('position__election', 'student').get(
                    code=vote_data['candidate_code']
                )
            except Candidate.DoesNotExist:
                raise serializers.ValidationError(f"Invalid candidate: {vote_data['candidate_code']}")

            position = candidate.position
            election = position.election

            if election.code != election_code:
                raise serializers.ValidationError("All votes must belong to the same election.")

            if user.current_level == 4:
                raise serializers.ValidationError("Level 400 students are not allowed to vote.")
            if not position.is_user_eligible(user):
                raise serializers.ValidationError(f"Not eligible for {position.title}")
            if not election.has_started():
                raise serializers.ValidationError("Election has not started yet.")
            if election.has_ended():
                raise serializers.ValidationError("Election has already ended.")
            if Vote.objects.filter(voter_did_hash=did_hash, position=position).exists():
                raise serializers.ValidationError(f"Already voted for {position.title}")

            if position.gender and position.gender != 'A':
                if not user.gender or user.gender.lower() != position.gender.lower():
                    raise serializers.ValidationError(
                        f"{position.title} restricted to {dict(GENDER_CHOICES).get(position.gender)} voters only."
                    )

            validated_votes.append({
                "candidate": candidate,
                "position": position,
                "election": election,
            })

        data['voter_did_hash'] = did_hash
        data['validated_votes'] = validated_votes
        return data

    def create(self, validated_data):
        from blockchain.helpers import cast_vote_batch
        from blockchain.utils import web3

        voter_did_hash = validated_data['voter_did_hash']
        validated_votes = validated_data['validated_votes']

        # Prepare arrays for Solidity voteBatch
        position_codes = []
        candidate_codes = []
        receipt_hashes = []

        for v in validated_votes:
            receipt_hash_hex = hexlify(os.urandom(32)).decode()
            position_codes.append(v["position"].code)
            candidate_codes.append(v["candidate"].code)
            receipt_hashes.append(receipt_hash_hex)

        try:
            with transaction.atomic():
                tx_receipt = cast_vote_batch(position_codes, candidate_codes, receipt_hashes)
                tx_hash = tx_receipt['transactionHash'].hex()

                block_number = tx_receipt.get('blockNumber')
                confirmations, block_timestamp = None, None
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

                # Save each vote locally
                created_votes = []
                for idx, v in enumerate(validated_votes):
                    vote = Vote.objects.create(
                        candidate=v["candidate"],
                        position=v["position"],
                        election=v["election"],
                        voter_did_hash=voter_did_hash,
                        receipt=receipt_hashes[idx],
                        tx_hash=tx_hash,
                        is_synced=True,
                        block_number=block_number,
                        block_confirmations=confirmations,
                        block_timestamp=block_timestamp,
                        status=status
                    )
                    created_votes.append(vote)

            return created_votes

        except Exception as e:
            logger.exception(f"Unexpected error during ballot voting: {e}")
            raise serializers.ValidationError("Ballot voting failed due to an unexpected error.")
