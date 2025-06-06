from django.contrib import admin
from django import forms
from elections.models import Election, Position, Candidate

# ---- Validation Form ----
class CandidateAdminForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")
        position = cleaned_data.get("position")

        if student and student.current_level == 4:
            raise forms.ValidationError("Students in Level 400 are not eligible to contest.")
        if position and not position.is_user_eligible(student):
            raise forms.ValidationError("This student does not belong to an eligible department for this position.")

        return cleaned_data


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'department', 'start_date', 'end_date', 'created_at')
    search_fields = ('title', 'department__name', 'code')
    ordering = ('-start_date',)
    list_filter = ('department', 'start_date')

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return [f for f in fields if f != 'code']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'election', 'get_eligible_levels', 'get_eligible_departments')
    search_fields = ('title', 'election__title', 'code')
    list_filter = ('election', 'eligible_departments')

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return [f for f in fields if f != 'code']

    def get_eligible_levels(self, obj):
        return ", ".join(f"Level {lvl * 100}" for lvl in obj.eligible_levels)
    get_eligible_levels.short_description = 'Eligible Levels'

    def get_eligible_departments(self, obj):
        return ", ".join([d.name for d in obj.eligible_departments.all()])
    get_eligible_departments.short_description = 'Eligible Departments'


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    form = CandidateAdminForm
    list_display = ('code', 'student', 'position', 'get_election')
    search_fields = ('student__full_name', 'position__title', 'code')
    list_filter = ('position__election', 'student__department')

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return [f for f in fields if f != 'code']

    def get_election(self, obj):
        return obj.position.election
    get_election.short_description = 'Election'
