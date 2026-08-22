from rest_framework import serializers

from .models import Table


class TableSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    open_order_id = serializers.SerializerMethodField()
    open_order_total = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = [
            "id",
            "number",
            "label",
            "is_helper",
            "location_note",
            "status",
            "open_order_id",
            "open_order_total",
        ]

    def get_status(self, obj):
        return "OCCUPIED" if obj.open_order else "FREE"

    def get_open_order_id(self, obj):
        order = obj.open_order
        return order.id if order else None

    def get_open_order_total(self, obj):
        order = obj.open_order
        return order.remaining_total if order else None


class TableLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ["location_note"]
