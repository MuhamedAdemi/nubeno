from django.core.management.base import BaseCommand

from tables.models import Table

# Numbered well above real tables (currently 1..14) so there's no risk of
# ever colliding with a genuine table number.
HELPER_TABLE_NUMBER_START = 1001


class Command(BaseCommand):
    help = (
        "Create helper tables F1..N (default 10) if they don't already exist — "
        "extra virtual registers for when one physical table has to be split "
        "into more separate bills than there are physical tables to spread "
        "them across."
    )

    def add_arguments(self, parser):
        parser.add_argument("count", nargs="?", type=int, default=10)

    def handle(self, *args, **options):
        count = options["count"]
        created = 0
        for i in range(1, count + 1):
            _, was_created = Table.objects.get_or_create(
                number=HELPER_TABLE_NUMBER_START + i - 1,
                defaults=dict(label=f"F{i}", is_helper=True),
            )
            created += was_created
        self.stdout.write(self.style.SUCCESS(f"{created} new helper table(s) created (F1..F{count})."))
