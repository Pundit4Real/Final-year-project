from rest_framework import serializers
from elections.models.elections import Election
from votes.models import Vote
from .positions import PositionNestedSerializer
import hashlib


def hash_did(did: str) -> str:
    """Hash the DID exactly as it's stored in Vote.voter_did_hash."""
    return hashlib.sha256(did.encode()).hexdigest()


class ElectionSerializer(serializers.ModelSerializer):
    has_voted = serializers.SerializerMethodField()
    total_candidates = serializers.IntegerField(read_only=True)
    total_positions = serializers.IntegerField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    status = serializers.ChoiceField(choices=Election.Status.choices, required=False)

    class Meta:
        model = Election
        fields = [
            'code', 'title', 'description', 'start_date', 'end_date',
            'created_at', 'has_voted', 'department_name', 'school_name',
            'total_candidates', 'total_positions', 'status'
        ]

    def get_has_voted(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        voter_hash = hash_did(request.user.did)
        return Vote.objects.filter(election=obj, voter_did_hash=voter_hash).exists()

    def create(self, validated_data):
        validated_data['status'] = Election.Status.DRAFT
        return super().create(validated_data)

    def to_internal_value(self, data):
        # prevent creating election with arbitrary status
        if self.instance is None and 'status' in data:
            data = dict(data)
            data.pop('status', None)
        return super().to_internal_value(data)

    def validate(self, attrs):
        """
        Prevent editing protected fields once election is synced.
        Allow only description to be updated.
        """
        if self.instance and self.instance.is_synced:
            allowed = {"description"}
            for field in attrs.keys():
                if field not in allowed:
                    raise serializers.ValidationError(
                        {field: "This field cannot be updated after blockchain sync."}
                    )
        return attrs


class ElectionDetailSerializer(serializers.ModelSerializer):
    positions = PositionNestedSerializer(many=True, read_only=True)
    is_active = serializers.SerializerMethodField()
    has_ended = serializers.SerializerMethodField()
    has_voted = serializers.SerializerMethodField()
    total_candidates = serializers.IntegerField(read_only=True)
    total_positions = serializers.IntegerField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    status = serializers.ChoiceField(choices=Election.Status.choices, required=False)

    class Meta:
        model = Election
        fields = [
            'code', 'title', 'description', 'start_date', 'end_date',
            'positions', 'is_active', 'has_ended',
            'has_voted', 'total_candidates', 'total_positions',
            'department_name', 'school_name', 'status'
        ]

    def get_is_active(self, obj):
        return obj.is_active()

    def get_has_ended(self, obj):
        return obj.has_ended()

    def get_has_voted(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        voter_hash = hash_did(request.user.did)
        return Vote.objects.filter(election=obj, voter_did_hash=voter_hash).exists()

    def to_internal_value(self, data):
        if self.instance is None and 'status' in data:
            data = dict(data)
            data.pop('status', None)
        return super().to_internal_value(data)

    def validate(self, attrs):
        """
        Same protection as ElectionSerializer.
        """
        if self.instance and self.instance.is_synced:
            allowed = {"description"}
            for field in attrs.keys():
                if field not in allowed:
                    raise serializers.ValidationError(
                        {field: "This field cannot be updated after blockchain sync."}
                    )
        return attrs
