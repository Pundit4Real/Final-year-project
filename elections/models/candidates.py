from django.db import models
from accounts.models import User
from accounts.utils import generate_code
from .positions import Position
from elections.directories import candidate_directory


class Candidate(models.Model):
    code = models.CharField(max_length=20, unique=True, blank=True)
    position = models.ForeignKey(Position, related_name='candidates', on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    manifesto = models.TextField(blank=True)
    image = models.ImageField(upload_to=candidate_directory, null=True, blank=True)
    campaign_keywords = models.CharField(max_length=255, blank=True, help_text="Comma-separated keywords for campaign")
    promise = models.TextField(blank=True, help_text="Main campaign promise or slogan")

    is_synced = models.BooleanField(default=False)
    last_synced = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('position', 'student')
        ordering = ['position']
        verbose_name = "Candidate"
        verbose_name_plural = "Candidates"

    def __str__(self):
        return f"{self.student.full_name} for {self.position.title}"

    def save(self, *args, **kwargs):
        if not self.code:
            school_name = None
            department_name = None
            scope = None

            if self.position and self.position.election:
                election = self.position.election
                if election.department:
                    department_name = election.department.name
                    scope = "Dept"
                elif election.school:
                    school_name = election.school.name
                    scope = "School"
                else:
                    scope = "Uni"
            else:
                scope = "Uni"

            self.code = generate_code(
                "CND",
                department_name=department_name,
                school_name=school_name,
                scope=scope,
                seq_length=3
            )
        super().save(*args, **kwargs)
