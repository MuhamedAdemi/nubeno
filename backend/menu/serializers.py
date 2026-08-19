from rest_framework import serializers

from .models import Category, MenuItem, ModifierGroup, ModifierOption


class ModifierOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModifierOption
        fields = ["id", "name_hr", "name_en", "name_sq"]


class ModifierGroupSerializer(serializers.ModelSerializer):
    options = ModifierOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ModifierGroup
        fields = ["id", "name_hr", "name_en", "name_sq", "options"]


class MenuItemSerializer(serializers.ModelSerializer):
    modifier_group = ModifierGroupSerializer(read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "name_hr",
            "name_en",
            "name_sq",
            "variant_label",
            "price",
            "modifier_group",
        ]


class CategorySerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name_hr", "name_en", "name_sq", "group", "items"]

    def get_items(self, obj):
        active_items = obj.items.filter(active=True)
        return MenuItemSerializer(active_items, many=True).data
