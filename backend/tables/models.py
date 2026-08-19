from django.db import models


class Table(models.Model):
    number = models.PositiveIntegerField(unique=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Table {self.number}"

    @property
    def open_order(self):
        return self.orders.filter(status="OPEN").first()
