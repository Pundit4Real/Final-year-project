from django.db import models
from django.utils import timezone
from accounts.models import Department
from accounts.utils import generate_code


class Election(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        UPCOMING = "upcoming", "Upcoming"
        ONGOING = "ongoing", "Ongoing"
        ENDED = "ended", "Ended"
        SUSPENDED = "suspended", "Suspended"
        CANCELLED = "cancelled", "Cancelled"

    code = models.CharField(max_length=10, unique=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

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
        return (
            self.status == self.Status.ONGOING
            and self.start_date <= now <= self.end_date
        )

    def has_started(self):
        return timezone.now() >= self.start_date

    def has_ended(self):
        return timezone.now() > self.end_date

    def get_status(self):
        return self.get_status_display()
