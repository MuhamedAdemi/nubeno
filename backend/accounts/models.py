from django.conf import settings
from django.db import models


class AdminProfile(models.Model):
    """Marks a small number of admin users as 'super admin' — protected from
    being edited or removed by any other admin (only another super admin, or
    themselves, can touch their account)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_profile"
    )
    is_super_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}{' (super admin)' if self.is_super_admin else ''}"
