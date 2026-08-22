from django.contrib import admin

from .models import Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ["number", "label", "is_helper", "location_note", "status"]
    list_filter = ["is_helper"]
    ordering = ["number"]

    @admin.display(description="Status")
    def status(self, obj):
        return "Occupied" if obj.open_order else "Free"
