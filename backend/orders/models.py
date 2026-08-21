from django.conf import settings
from django.db import models

from menu.models import MenuItem, ModifierOption
from tables.models import Table


class Order(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("PAID", "Paid"),
        ("CANCELLED", "Cancelled"),
    ]

    table = models.ForeignKey(Table, related_name="orders", on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="OPEN")
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-opened_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["table"],
                condition=models.Q(status="OPEN"),
                name="one_open_order_per_table",
            )
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.table} ({self.status})"

    @property
    def total(self):
        return sum((item.line_total for item in self.items.all()), start=0)

    @property
    def remaining_total(self):
        return sum((item.line_total for item in self.items.all() if not item.is_paid), start=0)


class OrderItem(models.Model):
    PAYMENT_METHOD_CHOICES = [("CASH", "Cash"), ("CARD", "Card"), ("MIXED", "Card + Cash")]

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    # Null for items paid before this field existed — every payment from now
    # on always sets it (required in PayItemsSerializer).
    payment_method = models.CharField(
        max_length=5, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True
    )
    # How much of this item's line_total was cash. Always set alongside
    # payment_method (line_total for CASH, 0 for CARD, a split amount for
    # MIXED) so cash-register reporting can sum this one field regardless of
    # which of the three payment_method values was used — see
    # CashRegisterView, which sums cash_portion for the cash total and
    # (line_total - cash_portion) for the card total.
    cash_portion = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.quantity}x {self.menu_item}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class OrderItemModifierRemoval(models.Model):
    order_item = models.ForeignKey(
        OrderItem, related_name="removed_modifiers", on_delete=models.CASCADE
    )
    modifier_option = models.ForeignKey(
        ModifierOption, related_name="removals", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ["order_item", "modifier_option"]


class CashRegisterEntry(models.Model):
    """One admin-set starting float ('polog') for the till. The state is
    continuous, not reset daily — the newest entry's amount + timestamp is
    the current baseline until an admin sets a new one (e.g. after counting
    the drawer), which is also why this is an append-only log rather than a
    single mutable row: it doubles as an audit trail."""

    float_amount = models.DecimalField(max_digits=8, decimal_places=2)
    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    set_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-set_at"]

    def __str__(self):
        return f"{self.float_amount} € as of {self.set_at:%Y-%m-%d %H:%M}"
