from django import forms
from django.core.exceptions import ValidationError
from elections.models.elections import Election
from elections.models.candidates import Candidate

class ElectionAdminForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        school = cleaned_data.get('school')
        department = cleaned_data.get('department')

        if school and department:
            raise ValidationError("You cannot select both a School and a Department. Please select only one.")

        return cleaned_data

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
            raise forms.ValidationError(
                "This student does not belong to an eligible department or level for this position."
            )
        return cleaned_data