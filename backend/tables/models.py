from django.db import models


class Table(models.Model):
    number = models.PositiveIntegerField(unique=True)
    # Blank for ordinary numbered tables (displayed as "Table {number}").
    # Set for helper tables (e.g. "F1") used as extra virtual registers when
    # one physical table has to be split into more bills than there are
    # physical tables for — see is_helper/location_note below.
    label = models.CharField(max_length=20, blank=True)
    is_helper = models.BooleanField(default=False)
    # Free text noting which physical table this helper table's food should
    # actually be delivered to (e.g. "Tavolina 3") — meaningless for
    # ordinary tables, where the table itself already is the location.
    location_note = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return self.label or f"Table {self.number}"

    @property
    def open_order(self):
        return self.orders.filter(status="OPEN").first()
