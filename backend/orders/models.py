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
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

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
