from django.db import models


class TranslatedNameMixin(models.Model):
    name_hr = models.CharField("Name (Croatian)", max_length=120)
    name_en = models.CharField("Name (English)", max_length=120)
    name_sq = models.CharField("Name (Albanian)", max_length=120)

    class Meta:
        abstract = True

    def name(self, lang: str) -> str:
        return getattr(self, f"name_{lang}", None) or self.name_hr

    def __str__(self):
        return self.name_en


class Category(TranslatedNameMixin):
    GROUP_CHOICES = [("FOOD", "Food"), ("DRINK", "Drink")]

    group = models.CharField(max_length=10, choices=GROUP_CHOICES)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name_plural = "Categories"


class ModifierGroup(TranslatedNameMixin):
    class Meta:
        ordering = ["id"]


class ModifierOption(TranslatedNameMixin):
    group = models.ForeignKey(
        ModifierGroup, related_name="options", on_delete=models.CASCADE
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["group", "order", "id"]


class MenuItem(TranslatedNameMixin):
    category = models.ForeignKey(
        Category, related_name="items", on_delete=models.CASCADE
    )
    variant_label = models.CharField(
        "Variant (e.g. 0.33l, Velika porcija)", max_length=60, blank=True
    )
    price = models.DecimalField(max_digits=6, decimal_places=2)
    modifier_group = models.ForeignKey(
        ModifierGroup,
        related_name="menu_items",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["category", "order", "id"]

    def __str__(self):
        label = f" ({self.variant_label})" if self.variant_label else ""
        return f"{self.name_en}{label}"
