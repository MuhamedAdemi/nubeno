from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from accounts.models import AdminProfile


class Command(BaseCommand):
    help = "Mark a user as the top-level super admin (protected from other admins in the Django admin)."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist:
            raise CommandError(f"No user named '{options['username']}'")

        profile, _ = AdminProfile.objects.get_or_create(user=user)
        profile.is_super_admin = True
        profile.save()
        self.stdout.write(self.style.SUCCESS(f"{user.username} is now the super admin."))
