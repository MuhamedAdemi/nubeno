from django.core.management.base import BaseCommand

from tables.models import Table


class Command(BaseCommand):
    help = "Create tables 1..N (default 14) if they don't already exist."

    def add_arguments(self, parser):
        parser.add_argument("count", nargs="?", type=int, default=14)

    def handle(self, *args, **options):
        count = options["count"]
        created = 0
        for n in range(1, count + 1):
            _, was_created = Table.objects.get_or_create(number=n)
            created += was_created
        self.stdout.write(self.style.SUCCESS(f"{created} new table(s) created (1..{count})."))
