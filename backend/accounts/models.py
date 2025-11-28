from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_USER = "USER"
    ROLE_ADMIN = "ADMIN"

    ROLE_CHOICES = (
        (ROLE_USER, "User"),
        (ROLE_ADMIN, "Admin"),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_USER,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_admin(self) -> bool:
        return self.role == self.ROLE_ADMIN
