from django.db import models
from accounts.models import Department
from ckeditor.fields import RichTextField
from accounts.utils import generate_code
from .elections import Election

GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    ('A', 'All'),
)

class Position(models.Model):
    code = models.CharField(max_length=20, unique=True, blank=True)
    election = models.ForeignKey(Election, related_name='positions', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = RichTextField(blank=True, null=True, help_text="short position description")
    eligible_levels = models.JSONField(default=list, help_text="List of eligible levels, e.g., [1, 2, 3]")
    eligible_departments = models.ManyToManyField(Department, blank=True)
    gender = models.CharField(max_length=1,choices=GENDER_CHOICES,default='A',
        help_text="Specify gender eligibility for this position."
    )

    is_synced = models.BooleanField(default=False)
    last_synced = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['election', 'title']
        verbose_name = "Position"
        verbose_name_plural = "Positions"

    def __str__(self):
        return f"{self.title} - {self.election.title}"
    
    def get_winner(self):
        """
        Returns the candidate with the highest votes for this position.
        If no votes exist, returns None.
        """
        from votes.models import Vote

        winner = (
            self.candidates  # ✅ reverse relation from Candidate → Position
            .annotate(vote_count=models.Count("votes"))  # count votes for each candidate
            .order_by("-vote_count")
            .first()
        )
        return winner

    def save(self, *args, **kwargs):
        if not self.code:
            school_name = None
            department_name = None
            scope = None

            if self.election and self.election.department:
                department_name = self.election.department.name
                scope = "Dept"
            elif self.election and self.election.school:
                school_name = self.election.school.name
                scope = "School"
            else:
                scope = "Uni"

            self.code = generate_code(
                "POS",
                department_name=department_name,
                school_name=school_name,
                scope=scope
            )
        super().save(*args, **kwargs)

    def is_user_eligible(self, user):
        """
        Check if a user meets level, department, and gender eligibility for this position.
        """
        level_ok = user.current_level in self.eligible_levels
        department_ok = (
            self.eligible_departments.count() == 0 or
            user.department in self.eligible_departments.all()
        )
        gender_ok = (
            self.gender == 'A' or
            user.gender == self.gender
        )
        return level_ok and department_ok and gender_ok
