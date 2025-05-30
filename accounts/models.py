from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from datetime import datetime
from .managers import UserManager

LEVEL_CHOICES = (
    (1, 'Level 100'),
    (2, 'Level 200'),
    (3, 'Level 300'),
    (4, 'Level 400'),
)

class User(AbstractBaseUser, PermissionsMixin):
    index_number = models.CharField(max_length=20, unique=True, default="UEB3502721")
    full_name = models.CharField(max_length=255)
    year_enrolled = models.IntegerField(default=datetime.now().year)
    email = models.EmailField(unique=True)
    did = models.CharField(max_length=100, unique=True)
    wallet_address = models.CharField(max_length=42, unique=True)
    private_key = models.TextField()
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
        current_year = datetime.now().year
        level = current_year - self.year_enrolled + 1
        return min(level, 4)