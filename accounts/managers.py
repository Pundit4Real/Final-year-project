from django.contrib.auth.models import BaseUserManager
from accounts.utils import generate_did

class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required.")

        # Only require department if not a superuser
        if not extra_fields.get("is_superuser") and not extra_fields.get("department"):
            raise ValueError("The Department field is required for regular users.")

        email = self.normalize_email(email)
        address, did, private_key = generate_did()
        user = self.model(
            email=email,
            full_name=full_name,
            did=did,
            wallet_address=address,
            private_key=private_key,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # Do NOT require department for superusers
        extra_fields.setdefault('department', None)

        return self.create_user(email, full_name, password, **extra_fields)
