from django.db import models
from accounts.models import Department
from accounts.utils import generate_code
from .elections import Election


class Position(models.Model):
    code = models.CharField(max_length=10, unique=True, blank=True)
    election = models.ForeignKey(Election, related_name='positions', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    eligible_levels = models.JSONField(default=list)  # Example: [1, 2, 3]
    eligible_departments = models.ManyToManyField(Department, blank=True)
    is_synced = models.BooleanField(default=False)
    last_synced_at = models.DateTimeField(null=True, blank=True)

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
