from django.db import models
# from datetime import datetime
from django.utils import timezone
from accounts.models import User, Department
from accounts.utils import generate_code

class Election(models.Model):
    code = models.CharField(max_length=10, unique=True, blank=True)
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

    def save(self, *args, **kwargs):
        if not self.code:
            scope = "Dept" if self.department else "Uni"
            dept_name = self.department.name if self.department else None
            self.code = generate_code("EL", department_name=dept_name, scope=scope)
        super().save(*args, **kwargs)


    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    def has_started(self):
        return timezone.now() >= self.start_date

    def has_ended(self):
        return timezone.now() > self.end_date


class Position(models.Model):
    code = models.CharField(max_length=10, unique=True, blank=True)
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

    def save(self, *args, **kwargs):
        if not self.code:
            dept_name = self.election.department.name if self.election and self.election.department else None
            scope = "Dept" if self.election and self.election.department else "Uni"
            self.code = generate_code("POS", department_name=dept_name, scope=scope)
        super().save(*args, **kwargs)


    def is_user_eligible(self, user):
        level_ok = user.current_level in self.eligible_levels
        department_ok = (
            self.eligible_departments.count() == 0 or
            user.department in self.eligible_departments.all()
        )
        return level_ok and department_ok


class Candidate(models.Model):
    code = models.CharField(max_length=12, unique=True, blank=True)
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

    def save(self, *args, **kwargs):
        if not self.code:
            dept_name = self.student.department.name if self.student and self.student.department else None
            scope = "Dept" if self.position and self.position.election and self.position.election.department else "Uni"
            self.code = generate_code("CND", department_name=dept_name, scope=scope, length=4)
        super().save(*args, **kwargs)
