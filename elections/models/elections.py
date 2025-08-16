from django.db import models
from django.utils import timezone
from accounts.models import Department, School
from accounts.utils import generate_code


class Election(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        UPCOMING = "upcoming", "Upcoming"
        ONGOING = "ongoing", "Ongoing"
        ENDED = "ended", "Ended"
        SUSPENDED = "suspended", "Suspended"
        CANCELLED = "cancelled", "Cancelled"

    code = models.CharField(max_length=20, unique=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    school = models.ForeignKey(
        School, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="elections"
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="elections"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_synced = models.BooleanField(default=False)
    last_synced = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Election"
        verbose_name_plural = "Elections"

    def __str__(self):
        return self.title

    def _compute_status(self):
        """Determine the status based on current date/time."""
        now = timezone.now()
        if self.status in [self.Status.SUSPENDED, self.Status.CANCELLED]:
            return self.status
        if now < self.start_date:
            return self.Status.UPCOMING
        elif self.start_date <= now <= self.end_date:
            return self.Status.ONGOING
        else:
            return self.Status.ENDED

    def refresh_status(self, save=False):
        """Refresh status dynamically; optionally save to DB."""
        new_status = self._compute_status()
        if self.status != new_status:
            self.status = new_status
            if save:
                super().save(update_fields=["status"])
        return self.status

    def save(self, *args, **kwargs):
        # Auto-generate code if missing
        if not self.code:
            school_name = None
            department_name = None
            scope = None
            if self.department:
                scope = "Dept"
                department_name = self.department.name
            elif self.school:
                scope = "School"
                school_name = self.school.name
            else:
                scope = "Uni"
            self.code = generate_code(
                "EL",
                department_name=department_name,
                school_name=school_name,
                scope=scope
            )
        # Ensure correct status before saving
        self.refresh_status(save=False)
        super().save(*args, **kwargs)

    def is_active(self):
        return self.refresh_status() == self.Status.ONGOING

    def has_started(self):
        return timezone.now() >= self.start_date

    def has_ended(self):
        return timezone.now() > self.end_date

    def get_status(self):
        return self.get_status_display()

    def has_voted(self, user):
        from votes.models import Vote
        return Vote.objects.filter(election=self, voter=user).exists()
