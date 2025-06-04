from django.db import models
from datetime import datetime
from django.utils import timezone
from accounts.models import User, Department

class Election(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Election"
        verbose_name_plural = "Elections"

    def __str__(self):
        return self.title
    
    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    def has_started(self):
        return timezone.now() >= self.start_date

    def has_ended(self):
        return timezone.now() > self.end_date


class Position(models.Model):
    election = models.ForeignKey(Election, related_name='positions', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    eligible_levels = models.JSONField(default=list)  # Example: [1, 2, 3]
    eligible_departments = models.ManyToManyField(Department, blank=True)

    class Meta:
        ordering = ['election', 'title']
        verbose_name = "Position"
        verbose_name_plural = "Positions"

    def __str__(self):
        return f"{self.title} - {self.election.title}"

    def is_user_eligible(self, user):
        level_ok = user.current_level in self.eligible_levels
        department_ok = (
            self.eligible_departments.count() == 0 or
            user.department in self.eligible_departments.all()
        )
        return level_ok and department_ok


class Candidate(models.Model):
    position = models.ForeignKey(Position, related_name='candidates', on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    manifesto = models.TextField(blank=True)

    class Meta:
        unique_together = ('position', 'student')
        ordering = ['position']
        verbose_name = "Candidate"
        verbose_name_plural = "Candidates"

    def __str__(self):
        return f"{self.student.full_name} for {self.position.title}"
