from rest_framework import serializers
from elections.models.candidates import Candidate


class ImageSerializerMixin(serializers.ModelSerializer):
    """Reusable mixin that provides an image field with absolute URL."""
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

    class Meta:
        abstract = True

class CandidateSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    position_code = serializers.CharField(source='position.code', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    election_title = serializers.CharField(source='position.election.title', read_only=True)
    image = serializers.SerializerMethodField()
    bio = serializers.CharField(required=False, allow_blank=True)
    manifesto = serializers.CharField(required=False, allow_blank=True)
    campaign_keywords = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Candidate
        fields = "__all__"
        read_only_fields = [
            'code',
            'student_name',
            'position_code',
            'position_title',
            'election_title',
            'student',
            'position',
        ]

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

    def validate(self, data):
        student = data.get('student', getattr(self.instance, 'student', None))
        position = data.get('position', getattr(self.instance, 'position', None))

        # Level 400 restriction
        if student and student.current_level == 4:
            raise serializers.ValidationError("Students in Level 400 are not eligible to contest.")

        # Eligibility check
        if position and student and not position.is_user_eligible(student):
            raise serializers.ValidationError(
                "This student is not eligible to contest for this position."
            )

        # One position per election
        if student and position:
            election = position.election
            existing = Candidate.objects.filter(
                student=student,
                position__election=election
            )
            if self.instance:  # exclude self on update
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError(
                    f"{student.full_name} is already contesting in this election "
                    f"for another position."
                )

        # Restrict fields if synced
        if self.instance and self.instance.is_synced:
            allowed = {"bio", "manifesto", "campaign_keywords", "image"}
            for field in data.keys():
                if field not in allowed:
                    raise serializers.ValidationError(
                        {field: "This field cannot be updated after blockchain sync."}
                    )

        return data


class CandidateNestedSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    image = serializers.SerializerMethodField()
    bio = serializers.CharField(required=False, allow_blank=True)
    manifesto = serializers.CharField(required=False, allow_blank=True)
    campaign_keywords = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Candidate
        fields = "__all__"
        read_only_fields = ['code', 'student', 'position']

