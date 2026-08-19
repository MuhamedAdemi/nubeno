from django.contrib import admin

from .models import Category, MenuItem, ModifierGroup, ModifierOption


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 0
    fields = ["name_hr", "name_en", "name_sq", "variant_label", "price", "modifier_group", "active", "order"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name_en", "name_hr", "name_sq", "group", "order"]
    list_filter = ["group"]
    inlines = [MenuItemInline]


class ModifierOptionInline(admin.TabularInline):
    model = ModifierOption
    extra = 0
    fields = ["name_hr", "name_en", "name_sq", "order"]


@admin.register(ModifierGroup)
class ModifierGroupAdmin(admin.ModelAdmin):
    list_display = ["name_en", "name_hr", "name_sq"]
    inlines = [ModifierOptionInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["name_en", "category", "variant_label", "price", "modifier_group", "active"]
    list_filter = ["category", "active"]
    search_fields = ["name_en", "name_hr", "name_sq"]
