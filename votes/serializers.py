from rest_framework import serializers
from votes.models import Vote
from elections.models import Candidate
from hashlib import sha256

class AnonymousVoteSerializer(serializers.ModelSerializer):
    candidate_code = serializers.CharField(write_only=True)
    position_code = serializers.CharField(write_only=True)
    election_code = serializers.CharField(write_only=True)

    class Meta:
        model = Vote
        fields = [
            'candidate_code', 'position_code', 'election_code',
            'timestamp', 'receipt'
        ]
        read_only_fields = ['timestamp', 'receipt']

    def validate(self, data):
        user = self.context['request'].user
        did = user.did

        if not did:
            raise serializers.ValidationError("User DID not found.")

        # Hash the DID
        did_hash = sha256(did.encode()).hexdigest()

        # Fetch candidate using the code
        try:
            candidate = Candidate.objects.select_related('position__election').get(code=data['candidate_code'])
        except Candidate.DoesNotExist:
            raise serializers.ValidationError("Invalid candidate code.")

        position = candidate.position
        election = position.election

        # Ensure code consistency
        if data['position_code'] != position.code:
            raise serializers.ValidationError("Position code mismatch.")
        if data['election_code'] != election.code:
            raise serializers.ValidationError("Election code mismatch.")

        # Check eligibility and election status
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

        # Pass the validated fields
        data['voter_did_hash'] = did_hash
        data['position'] = position
        data['election'] = election
        data['candidate'] = candidate
        return data

    def create(self, validated_data):
        # Clean up non-model fields
        validated_data.pop('candidate_code', None)
        validated_data.pop('position_code', None)
        validated_data.pop('election_code', None)
        return Vote.objects.create(**validated_data)
