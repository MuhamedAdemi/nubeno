from django.core.management.base import BaseCommand
from django.db import transaction

from orders.models import CashRegisterEntry, Order


class Command(BaseCommand):
    help = (
        "Permanently deletes ALL orders (and their items) and ALL cash-register "
        "float history — a hard reset back to zero evidence. Tables, the menu, "
        "and staff accounts are untouched. Defaults to a dry run; pass --yes to "
        "actually delete."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes", action="store_true", help="Actually delete. Without this flag, only reports counts."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        order_count = Order.objects.count()
        cash_entry_count = CashRegisterEntry.objects.count()

        if not options["yes"]:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN — would permanently delete {order_count} order(s) (and their items) "
                    f"and {cash_entry_count} cash-register entry(ies).\n"
                    "Nothing was deleted. Re-run with --yes to actually delete."
                )
            )
            return

        Order.objects.all().delete()
        CashRegisterEntry.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {order_count} order(s) and {cash_entry_count} cash-register entry(ies). "
                "Tables, the menu, and staff accounts are untouched."
            )
        )
