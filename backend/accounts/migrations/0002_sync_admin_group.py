from django.db import migrations


def sync_existing_admins(apps, schema_editor):
    """One-off backfill: accounts created before the admin-permissions
    signal existed (accounts/signals.py) need the same group membership
    applied retroactively, or an already-created regular admin (is_staff,
    not superuser) would still have no permissions to manage other users
    until their account happened to be re-saved.

    Uses the real (not historical/frozen) User/Group models — safe here
    since none of their relevant fields have changed shape, and it lets
    this reuse the exact same logic the signal applies going forward."""
    from django.contrib.auth import get_user_model

    from accounts.signals import sync_admin_group_membership

    User = get_user_model()
    for user in User.objects.all():
        sync_admin_group_membership(User, user)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(sync_existing_admins, noop_reverse),
    ]
