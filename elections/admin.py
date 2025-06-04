from django.contrib import admin
from django import forms
from elections.models import Election, Position, Candidate


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'start_date', 'end_date', 'created_at')
    search_fields = ('title', 'department__name')
    ordering = ('-start_date',)
    list_filter = ('department', 'start_date')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'election', 'get_eligible_levels', 'get_eligible_departments')
    search_fields = ('title', 'election__title')
    list_filter = ('election', 'eligible_departments')

    def get_eligible_levels(self, obj):
        return ", ".join(f"Level {lvl * 100}" for lvl in obj.eligible_levels)
    get_eligible_levels.short_description = 'Eligible Levels'

    def get_eligible_departments(self, obj):
        return ", ".join([d.name for d in obj.eligible_departments.all()])
    get_eligible_departments.short_description = 'Eligible Departments'


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



@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    form = CandidateAdminForm
    list_display = ('student', 'position', 'get_election')
    search_fields = ('student__full_name', 'position__title')
    list_filter = ('position__election', 'student__department')

    def get_election(self, obj):
        return obj.position.election
    get_election.short_description = 'Election'
