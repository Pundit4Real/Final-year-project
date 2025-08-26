from django import forms
from django.core.exceptions import ValidationError
from elections.models.elections import Election
from elections.models.candidates import Candidate
from accounts.models import GENDER_CHOICES

class ElectionAdminForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        school = cleaned_data.get('school')
        department = cleaned_data.get('department')

        if school and department:
            raise ValidationError(
                "You cannot select both a School and a Department. Please select only one."
            )

        return cleaned_data


class CandidateAdminForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")
        position = cleaned_data.get("position")

        # 1. Level 400 restriction
        if student and student.current_level == 4:
            raise forms.ValidationError(
                "Students in Level 400 are not eligible to contest."
            )

        # 2. Department/level eligibility
        if position and not position.is_user_eligible(student):
            raise forms.ValidationError(
                "This student does not belong to an eligible department or level for this position."
            )

        # 3. Gender restriction (unless 'A' = All)
        if position and position.gender and position.gender != 'A':
            if not student or student.gender != position.gender:
                raise forms.ValidationError(
                    f"This position is restricted to "
                    f"{dict(GENDER_CHOICES).get(position.gender)} candidates."
                )

        # 4. Ensure student is not contesting two positions in the same election
        if student and position:
            election = position.election
            existing = Candidate.objects.filter(
                student=student,
                position__election=election
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(
                    f"{student.full_name} is already contesting in this election "
                    f"for another position."
                )

        return cleaned_data
