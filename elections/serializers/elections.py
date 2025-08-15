from rest_framework import serializers
from elections.models.elections import Election
from .positions import PositionNestedSerializer


class ElectionSerializer(serializers.ModelSerializer):
    has_voted = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    total_candidates = serializers.IntegerField(read_only=True)
    total_positions = serializers.IntegerField(read_only=True)
    # Make status readable but conditionally writable
    status = serializers.ChoiceField(
        choices=Election.Status.choices,
        required=False
    )

    class Meta:
        model = Election
        fields = [
            'code', 'title', 'description', 'start_date', 'end_date',
            'created_at', 'has_voted', 'department_name', 'school_name',
            'total_candidates', 'total_positions', 'status'
        ]

    def get_has_voted(self, obj):
        if hasattr(obj, 'has_voted'):
            return bool(obj.has_voted)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.has_voted(request.user)
        return False

    def create(self, validated_data):
        validated_data['status'] = Election.Status.DRAFT
        return super().create(validated_data)

    def to_internal_value(self, data):
        # Prevent setting status at creation
        if self.instance is None and 'status' in data:
            data = dict(data)
            data.pop('status', None)
        return super().to_internal_value(data)


class ElectionDetailSerializer(serializers.ModelSerializer):
    positions = PositionNestedSerializer(many=True, read_only=True)
    is_active = serializers.SerializerMethodField()
    has_ended = serializers.SerializerMethodField()
    has_voted = serializers.SerializerMethodField()
    total_candidates = serializers.IntegerField(read_only=True)
    total_positions = serializers.IntegerField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    status = serializers.ChoiceField(
        choices=Election.Status.choices,
        required=False
    )

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
        if hasattr(obj, 'has_voted'):
            return bool(obj.has_voted)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.has_voted(request.user)
        return False

    def to_internal_value(self, data):
        # Prevent setting status at creation
        if self.instance is None and 'status' in data:
            data = dict(data)
            data.pop('status', None)
        return super().to_internal_value(data)
