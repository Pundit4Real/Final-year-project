from django.db import models
from accounts.models import User
from datetime import datetime

class Election(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Election"
        verbose_name_plural = "Elections"

    def __str__(self):
        return self.title
    
    def is_active(self):
        now = datetime.now()
        return self.start_date <= now <= self.end_date

    def has_started(self):
        return datetime.now() >= self.start_date

    def has_ended(self):
        return datetime.now() > self.end_date


class Position(models.Model):
    election = models.ForeignKey(Election, related_name='positions', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    eligible_levels = models.JSONField(default=list)  # Example: [1, 2, 3]

    class Meta:
        ordering = ['election', 'title']
        verbose_name = "Position"
        verbose_name_plural = "Positions"

    def __str__(self):
        return f"{self.title} - {self.election.title}"

    def is_user_eligible(self, user):
        return user.current_level in self.eligible_levels


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
