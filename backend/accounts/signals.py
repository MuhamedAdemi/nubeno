from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver

ADMIN_GROUP_NAME = "Restaurant Admins"

# Permission codenames a regular admin (is_staff, not superuser) needs to
# create/manage waiter and admin accounts from Django admin. AdminProfile
# permissions are included so the super-admin inline is even visible on the
# user form — without view/add/change on it, Django admin hides the inline
# entirely regardless of the field-level read-only logic in accounts/admin.py.
ADMIN_GROUP_PERMISSIONS = [
    ("auth", "add_user"),
    ("auth", "change_user"),
    ("auth", "delete_user"),
    ("auth", "view_user"),
    ("accounts", "add_adminprofile"),
    ("accounts", "change_adminprofile"),
    ("accounts", "view_adminprofile"),
]


def _get_or_create_admin_group() -> Group:
    group, created = Group.objects.get_or_create(name=ADMIN_GROUP_NAME)
    if created:
        perms = Permission.objects.filter(
            content_type__app_label__in={app for app, _ in ADMIN_GROUP_PERMISSIONS},
            codename__in={code for _, code in ADMIN_GROUP_PERMISSIONS},
        )
        group.permissions.set(perms)
    return group


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def sync_admin_group_membership(sender, instance, **kwargs):
    """Keeps every non-superuser admin (is_staff=True) able to create and
    manage waiter/admin accounts in Django admin, without hand-granting
    permissions each time — a plain is_staff=True user has none by default
    and couldn't actually add or edit other users otherwise."""
    group = _get_or_create_admin_group()
    if instance.is_staff and not instance.is_superuser:
        instance.groups.add(group)
    else:
        instance.groups.remove(group)
