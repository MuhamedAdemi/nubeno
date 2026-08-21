from rest_framework import serializers

from menu.models import MenuItem, ModifierOption
from menu.serializers import MenuItemSerializer, ModifierOptionSerializer
from tables.models import Table

from .models import CashRegisterEntry, Order, OrderItem, OrderItemModifierRemoval


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)
    removed_modifiers = serializers.SerializerMethodField()
    line_total = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "menu_item",
            "quantity",
            "unit_price",
            "note",
            "removed_modifiers",
            "line_total",
            "is_paid",
            "payment_method",
        ]

    def get_removed_modifiers(self, obj):
        options = ModifierOption.objects.filter(removals__order_item=obj)
        return ModifierOptionSerializer(options, many=True).data


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    remaining_total = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    table_number = serializers.IntegerField(source="table.number", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "table",
            "table_number",
            "status",
            "opened_by",
            "opened_at",
            "closed_at",
            "items",
            "total",
            "remaining_total",
        ]
        read_only_fields = ["status", "opened_by", "opened_at", "closed_at"]


class AddOrderItemSerializer(serializers.Serializer):
    menu_item_id = serializers.PrimaryKeyRelatedField(
        source="menu_item", queryset=MenuItem.objects.filter(active=True)
    )
    quantity = serializers.IntegerField(min_value=1, default=1)
    note = serializers.CharField(max_length=200, required=False, allow_blank=True)
    removed_modifier_option_ids = serializers.PrimaryKeyRelatedField(
        source="removed_modifier_options",
        queryset=ModifierOption.objects.all(),
        many=True,
        required=False,
        default=list,
    )

    def create(self, validated_data):
        order = self.context["order"]
        menu_item = validated_data["menu_item"]
        removed_options = validated_data.get("removed_modifier_options", [])

        order_item = OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=validated_data.get("quantity", 1),
            unit_price=menu_item.price,
            note=validated_data.get("note", ""),
        )
        OrderItemModifierRemoval.objects.bulk_create(
            [
                OrderItemModifierRemoval(order_item=order_item, modifier_option=opt)
                for opt in removed_options
            ]
        )
        return order_item


class UpdateOrderItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, required=False)
    note = serializers.CharField(max_length=200, required=False, allow_blank=True)
    removed_modifier_option_ids = serializers.PrimaryKeyRelatedField(
        source="removed_modifier_options",
        queryset=ModifierOption.objects.all(),
        many=True,
        required=False,
    )

    def update(self, instance, validated_data):
        if "quantity" in validated_data:
            instance.quantity = validated_data["quantity"]
        if "note" in validated_data:
            instance.note = validated_data["note"]
        instance.save()

        if "removed_modifier_options" in validated_data:
            instance.removed_modifiers.all().delete()
            OrderItemModifierRemoval.objects.bulk_create(
                [
                    OrderItemModifierRemoval(order_item=instance, modifier_option=opt)
                    for opt in validated_data["removed_modifier_options"]
                ]
            )
        return instance


class PayItemsSerializer(serializers.Serializer):
    item_ids = serializers.PrimaryKeyRelatedField(
        queryset=OrderItem.objects.all(), many=True, required=False, default=list
    )
    payment_method = serializers.ChoiceField(choices=OrderItem.PAYMENT_METHOD_CHOICES)
    # Only meaningful (and required) for MIXED — how much of this payment was
    # cash; the rest is treated as card. Validated against the actual total
    # being paid in the view, since that total isn't known until item_ids is
    # resolved against the order.
    cash_amount = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, min_value=0)

    def validate(self, data):
        if data["payment_method"] == "MIXED" and "cash_amount" not in data:
            raise serializers.ValidationError({"cash_amount": "Required when payment_method is MIXED."})
        return data


class TransferOrderSerializer(serializers.Serializer):
    table_id = serializers.PrimaryKeyRelatedField(source="table", queryset=Table.objects.all())

    def validate_table_id(self, table):
        if table.open_order:
            raise serializers.ValidationError("That table already has an open order.")
        return table


class CashRegisterStateSerializer(serializers.Serializer):
    float_amount = serializers.DecimalField(max_digits=8, decimal_places=2)
    set_at = serializers.DateTimeField(allow_null=True)
    set_by_username = serializers.CharField(allow_null=True)
    cash_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    card_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    expected_cash = serializers.DecimalField(max_digits=10, decimal_places=2)


class SetCashFloatSerializer(serializers.Serializer):
    float_amount = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0)

    def create(self, validated_data):
        return CashRegisterEntry.objects.create(
            float_amount=validated_data["float_amount"], set_by=self.context["request"].user
        )
