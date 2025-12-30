from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom user model.
    We keep username + password (no phone, no email required).
    This gives us flexibility later if we want to extend.
    """
    # username field already exists in AbstractUser
    # password field already exists

    def __str__(self):
        return self.username
