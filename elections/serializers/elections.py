from rest_framework import serializers
from elections.models.elections import Election
from .positions import PositionNestedSerializer


class ElectionSerializer(serializers.ModelSerializer):
    has_started = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    # Make status readable but conditionally writable
    status = serializers.ChoiceField(
        choices=Election.Status.choices,
        required=False
    )

    class Meta:
        model = Election
        fields = [
            'title', 'description', 'start_date', 'end_date',
            'created_at', 'has_started', 'department_name', 'status'
        ]

    def get_has_started(self, obj):
        return obj.has_started()

    def create(self, validated_data):
        # Force new elections to start as "draft"
        validated_data['status'] = Election.Status.DRAFT
        return super().create(validated_data)

    def to_internal_value(self, data):
        """
        Prevent 'status' from being set during creation.
        Allow it only during updates.
        """
        if self.instance is None and 'status' in data:
            data = dict(data)  # make mutable copy
            data.pop('status', None)
        return super().to_internal_value(data)


class ElectionDetailSerializer(serializers.ModelSerializer):
    positions = PositionNestedSerializer(many=True, read_only=True)
    has_started = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    has_ended = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    status = serializers.ChoiceField(
        choices=Election.Status.choices,
        required=False
    )

    class Meta:
        model = Election
        fields = [
            'code', 'title', 'description', 'start_date', 'end_date',
            'positions', 'has_started', 'is_active', 'has_ended',
            'department_name', 'status'
        ]

    def get_has_started(self, obj):
        return obj.has_started()

    def get_is_active(self, obj):
        return obj.is_active()

    def get_has_ended(self, obj):
        return obj.has_ended()

    def to_internal_value(self, data):
        """
        Prevent 'status' from being set during creation for detail serializer too.
        """
        if self.instance is None and 'status' in data:
            data = dict(data)
            data.pop('status', None)
        return super().to_internal_value(data)
