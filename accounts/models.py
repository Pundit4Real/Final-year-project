from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from datetime import datetime
from accounts.managers import UserManager
from accounts.utils import generate_did

LEVEL_CHOICES = (
    (1, 'Level 100'),
    (2, 'Level 200'),
    (3, 'Level 300'),
    (4, 'Level 400'),
)

class School(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    school = models.ForeignKey(School,on_delete=models.CASCADE,null=True,related_name="departments")

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        if self.school:
            return f"{self.name} ({self.school.name})"
        return self.name



class User(AbstractBaseUser, PermissionsMixin):
    index_number = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255)
    year_enrolled = models.IntegerField(default=datetime.now().year)
    level = models.IntegerField(choices=LEVEL_CHOICES, null=True, blank=True)

    department = models.ForeignKey(Department,on_delete=models.PROTECT,null=True,blank=True
    )
    email = models.EmailField(unique=True)
    did = models.CharField(max_length=100, unique=True, blank=True)
    wallet_address = models.CharField(max_length=42, unique=True, blank=True)
    private_key = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'index_number'
    REQUIRED_FIELDS = ['full_name', 'email']

    objects = UserManager()

    def __str__(self):
        return self.index_number

    @property
    def current_level(self):
        if self.level:
            return self.level
        current_year = datetime.now().year
        return min(current_year - self.year_enrolled + 1, 4)

    @property
    def role(self):
        if self.is_superuser:
            return "Admin"
        elif self.is_staff:
            return "Staff"
        return "Student"

    @property
    def status(self):
        current_year = datetime.now().year
        graduated = (current_year - self.year_enrolled) > 4
        if graduated:
            return "Inactive"
        if not self.is_active:
            return "Suspended"
        return "Active"

    def save(self, *args, **kwargs):
        if not self.did or not self.wallet_address or not self.private_key:
            address, did, private_key = generate_did()
            self.wallet_address = address
            self.did = did
            self.private_key = private_key
        super().save(*args, **kwargs)


