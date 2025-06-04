from rest_framework import serializers
from votes.models import Vote
# from elections.models import Candidate, Position, Election
from hashlib import sha256

class AnonymousVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['id', 'candidate', 'position', 'election', 'timestamp', 'receipt']
        read_only_fields = ['id', 'timestamp', 'receipt']

    def validate(self, data):
        user = self.context['request'].user
        did = user.did

        if not did:
            raise serializers.ValidationError("User DID not found.")

        did_hash = sha256(did.encode()).hexdigest()

        candidate = data.get('candidate')
        position = data.get('position')
        election = data.get('election')

        if user.current_level == 4:
            raise serializers.ValidationError("Level 400 students are not allowed to vote.")

        if candidate.position != position:
            raise serializers.ValidationError("Candidate does not match the selected position.")

        if position.election != election:
            raise serializers.ValidationError("Position does not belong to the specified election.")

        if not election.has_started():
            raise serializers.ValidationError("The election has not started yet.")

        if election.has_ended():
            raise serializers.ValidationError("The election has already ended.")

        if Vote.objects.filter(voter_did_hash=did_hash, position=position).exists():
            raise serializers.ValidationError("You have already voted for this position.")

        data['voter_did_hash'] = did_hash
        return data
