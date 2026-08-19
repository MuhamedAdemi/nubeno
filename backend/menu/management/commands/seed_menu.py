from django.core.management.base import BaseCommand
from django.db import transaction

from menu.models import Category, MenuItem, ModifierGroup, ModifierOption

# (hr, en, sq, group, order) — consolidated back to a handful of tabs (owner
# tried the finer 7-tab split and asked to return to this, matching a
# reference POS layout where "Food" is one grid grouped by item type).
CATEGORIES = {
    "pizza": ("Pizza", "Pizza", "Pica", "FOOD", 10),
    "sallata": ("Salate", "Salads", "Sallata", "FOOD", 20),
    "hrana": ("Hrana", "Food", "Ushqim", "FOOD", 30),
    "alkoolike": ("Alkoholna Pića", "Alcoholic Drinks", "Pije Alkoolike", "DRINK", 40),
    "pije": ("Bezalkoholna Pića", "Soft Drinks", "Pije Freskuese", "DRINK", 50),
}

# Every group below is an *optional* customize list — the waiter only opens
# it when asked to remove something; tapping the item itself always adds the
# standard recipe. (hr, en, sq, [(opt_hr, opt_en, opt_sq), ...])
MODIFIER_GROUPS = {
    # Shared by burger / tortilla / kebab / plata items.
    "food_extras": (
        "Dodaci (burger/kebab/tortilja)",
        "Extras (burger/kebab/tortilla)",
        "Shtesa (burger/kebab/tortilja)",
        [
            ("Kečap", "Ketchup", "Salcë Ketchup"),
            ("Majoneza", "Mayo", "Majonezë"),
            ("Umak", "Sauce", "Salcë"),
            ("Zelena salata", "Lettuce", "Sallatë jeshile"),
            ("Kupus", "Cabbage", "Lakër"),
            ("Paradajz", "Tomato", "Domate"),
            ("Luk", "Onion", "Qepë"),
            ("Krastavac", "Cucumber", "Kastravec"),
            ("Kukuruz", "Corn", "Misër"),
            ("Mrkva", "Carrot", "Karrotë"),
        ],
    ),
    # Pizza ingredient lists, taken from the menu's own descriptions.
    "pz_margherita": ("Margherita sastojci", "Margherita ingredients", "Përbërësit e Margheritës", [
        ("Pelati", "Tomato Sauce", "Salcë Domate"), ("Sir", "Cheese", "Djathë"),
    ]),
    "pz_funghi": ("Funghi sastojci", "Funghi ingredients", "Përbërësit e Funghi", [
        ("Pelati", "Tomato Sauce", "Salcë Domate"), ("Sir", "Cheese", "Djathë"),
        ("Gljive", "Mushrooms", "Kërpudha"),
    ]),
    "pz_vezuvio": ("Vezuvio sastojci", "Vezuvio ingredients", "Përbërësit e Vezuvios", [
        ("Pelati", "Tomato Sauce", "Salcë Domate"), ("Sir", "Cheese", "Djathë"),
        ("Šunka", "Ham", "Proshutë"), ("Masline", "Olives", "Ullinj"),
    ]),
    "pz_ruccola": ("Ruccola pizza sastojci", "Ruccola pizza ingredients", "Përbërësit e picës Ruccola", [
        ("Pelati", "Tomato Sauce", "Salcë Domate"), ("Sir", "Cheese", "Djathë"),
        ("Rukola", "Rucola", "Rukola"),
    ]),
    "pz_vegetariana": ("Vegetariana sastojci", "Vegetariana ingredients", "Përbërësit e Vegetarianas", [
        ("Pelati", "Tomato Sauce", "Salcë Domate"), ("Sir", "Cheese", "Djathë"),
        ("Kukuruz", "Corn", "Misër"), ("Rajčica", "Tomato", "Domate"),
        ("Paprika", "Bell Pepper", "Spec"), ("Krastavci", "Cucumber", "Kastravec"),
        ("Tikvice", "Zucchini", "Kungull"),
    ]),
    "pz_mexicana": ("Mexicana sastojci", "Mexicana ingredients", "Përbërësit e Mexicanas", [
        ("Pelati", "Tomato Sauce", "Salcë Domate"), ("Sir", "Cheese", "Djathë"),
        ("Ljuti kulen", "Hot Kulen Sausage", "Suxhuk Djegës"),
        ("Ljuta paprika", "Hot Pepper", "Spec Djegës"), ("Feferoni", "Chili Peppers", "Feferona"),
    ]),
    "pz_capricciosa": ("Capricciosa sastojci", "Capricciosa ingredients", "Përbërësit e Capricciosas", [
        ("Pelati", "Tomato Sauce", "Salcë Domate"), ("Sir", "Cheese", "Djathë"),
        ("Gljive", "Mushrooms", "Kërpudha"), ("Šunka", "Ham", "Proshutë"), ("Masline", "Olives", "Ullinj"),
    ]),
    "pz_buffala": ("Buffala sastojci", "Buffala ingredients", "Përbërësit e Buffalas", [
        ("Pelati", "Tomato Sauce", "Salcë Domate"), ("Mozzarella", "Mozzarella", "Mocarela"),
        ("Bosiljak", "Basil", "Borzilok"),
    ]),
    "pz_tonno": ("Tonno sastojci", "Tonno ingredients", "Përbërësit e Tonno", [
        ("Pelati", "Tomato Sauce", "Salcë Domate"), ("Sir", "Cheese", "Djathë"),
        ("Tuna", "Tuna", "Tuna"), ("Luk", "Onion", "Qepë"),
    ]),
    "pz_napoletana": ("Napoletana sastojci", "Napoletana ingredients", "Përbërësit e Napoletanas", [
        ("Pelati", "Tomato Sauce", "Salcë Domate"), ("Sir", "Cheese", "Djathë"),
        ("Gljive", "Mushrooms", "Kërpudha"), ("Šunka", "Ham", "Proshutë"), ("Vrhnje", "Cream", "Krem"),
    ]),
    "pz_calzone": ("Calzone sastojci", "Calzone ingredients", "Përbërësit e Calzones", [
        ("Pelati", "Tomato Sauce", "Salcë Domate"), ("Sir", "Cheese", "Djathë"),
        ("Gljive", "Mushrooms", "Kërpudha"), ("Šunka", "Ham", "Proshutë"), ("Masline", "Olives", "Ullinj"),
    ]),
    "pz_quatro": ("Quatro Formaggi sastojci", "Quatro Formaggi ingredients", "Përbërësit e Quatro Formaggi", [
        ("Pelati", "Tomato Sauce", "Salcë Domate"), ("Sir", "Cheese", "Djathë"),
        ("Mozzarella", "Mozzarella", "Mocarela"), ("Gorgonzola", "Gorgonzola", "Gorgonzola"),
        ("Grabancijaš", "Grabancijaš", "Grabancijaš"),
    ]),
    "pz_nubeno": ("Nubeno pizza sastojci", "Nubeno pizza ingredients", "Përbërësit e picës Nubeno", [
        ("Pelati", "Tomato Sauce", "Salcë Domate"), ("Sir", "Cheese", "Djathë"),
        ("Govedi pršut", "Smoked Beef Ham", "Proshutë Viçi"), ("Rukola", "Rucola", "Rukola"),
        ("Vrhnje", "Cream", "Krem"), ("Cherry rajčice", "Cherry Tomato", "Domate Cherry"),
        ("Masline", "Olives", "Ullinj"),
    ]),
    # Salad ingredient lists.
    "sl_sopska": ("Šopska sastojci", "Shop Salad ingredients", "Përbërësit e Sallatës Shopska", [
        ("Krastavci", "Cucumbers", "Kastravec"), ("Rajčica", "Tomato", "Domate"),
        ("Feta sir", "Feta Cheese", "Djathë Feta"), ("Masline", "Olives", "Ullinj"),
    ]),
    "sl_ruccola": ("Ruccola salata sastojci", "Ruccola salad ingredients", "Përbërësit e Sallatës Rukola", [
        ("Rukola", "Rucola", "Rukola"), ("Cherry rajčice", "Cherry Tomato", "Domate Cherry"),
        ("Parmezan", "Parmesan", "Parmezan"), ("Kukuruz", "Corn", "Misër"),
    ]),
    "sl_grcka": ("Grčka sastojci", "Greek Salad ingredients", "Përbërësit e Sallatës Greke", [
        ("Krastavci", "Cucumbers", "Kastravec"), ("Rajčica", "Tomato", "Domate"),
        ("Feta sir", "Feta Cheese", "Djathë Feta"), ("Masline", "Olives", "Ullinj"), ("Luk", "Onion", "Qepë"),
    ]),
    "sl_tuna": ("Tuna salata sastojci", "Tuna salad ingredients", "Përbërësit e Sallatës Tuna", [
        ("Krastavci", "Cucumbers", "Kastravec"), ("Rajčica", "Tomato", "Domate"),
        ("Zelena salata", "Lettuce", "Sallatë jeshile"), ("Tuna", "Tuna", "Tuna"),
        ("Luk", "Onion", "Qepë"), ("Masline", "Olives", "Ullinj"),
    ]),
    "sl_caprese": ("Caprese sastojci", "Caprese ingredients", "Përbërësit e Caprese", [
        ("Rajčica", "Tomato", "Domate"), ("Mozzarella", "Mozzarella", "Mocarela"),
        ("Bosiljak", "Basil", "Borzilok"),
    ]),
    "sl_cezar": ("Cezar sastojci", "Caesar Salad ingredients", "Përbërësit e Sallatës Cezar", [
        ("Zelena salata", "Lettuce", "Sallatë jeshile"), ("Piletina", "Chicken", "Pule"),
        ("Umak", "Sauce", "Salcë"), ("Cherry rajčice", "Cherry Tomato", "Domate Cherry"),
        ("Grana padana", "Grana Padana", "Grana Padana"), ("Kockice kruha", "Bread Croutons", "Kub Buke"),
    ]),
    "sl_pileca": ("Pileća salata sastojci", "Chicken Salad ingredients", "Përbërësit e Sallatës me Pule", [
        ("Zelena salata", "Lettuce", "Sallatë jeshile"), ("Rajčica", "Tomato", "Domate"),
        ("Krastavci", "Cucumbers", "Kastravec"), ("Kukuruz", "Corn", "Misër"),
        ("Piletina", "Chicken", "Pule"), ("Masline", "Olives", "Ullinj"),
    ]),
}

# category_key, [(name_hr, name_en, name_sq, variant_label, price, modifier_group_key)]
ITEMS = {
    "pizza": [
        ("Margherita", "Margherita", "Margherita", "", "10.00", "pz_margherita"),
        ("Funghi", "Funghi", "Funghi", "", "12.00", "pz_funghi"),
        ("Vezuvio", "Vezuvio", "Vezuvio", "", "13.00", "pz_vezuvio"),
        ("Ruccola", "Ruccola", "Rukola", "", "12.00", "pz_ruccola"),
        ("Vegetariana", "Vegetariana", "Vegetariana", "", "12.50", "pz_vegetariana"),
        ("Mexicana", "Mexicana", "Mexicana", "", "13.00", "pz_mexicana"),
        ("Capricciosa", "Capricciosa", "Capricciosa", "", "13.00", "pz_capricciosa"),
        ("Buffala", "Buffala", "Buffala", "", "13.00", "pz_buffala"),
        ("Tonno", "Tonno", "Tonno", "", "13.50", "pz_tonno"),
        ("Napoletana", "Napoletana", "Napoletana", "", "14.00", "pz_napoletana"),
        ("Calzone", "Calzone", "Calzone", "", "14.00", "pz_calzone"),
        ("Quatro Formaggi", "Quatro Formaggi", "Quatro Formaggi", "", "14.00", "pz_quatro"),
        ("Nubeno", "Nubeno", "Nubeno", "", "16.00", "pz_nubeno"),
        ("Pizza kriška", "Pizza Slice", "Fetë Pice", "", "4.00", None),
        ("Pogača", "Flatbread", "Pogaçe", "", "6.00", None),
    ],
    "sallata": [
        ("Miješana", "Mixed Salad", "Sallatë e Përzier", "", "8.50", None),
        ("Šopska", "Shop Salad", "Sallatë Shopska", "", "8.50", "sl_sopska"),
        ("Ruccola", "Ruccola", "Rukola", "", "9.00", "sl_ruccola"),
        ("Grčka", "Greek Salad", "Sallatë Greke", "", "9.50", "sl_grcka"),
        ("Tuna", "Tuna", "Tuna", "", "9.50", "sl_tuna"),
        ("Caprese Salata", "Caprese Salad", "Sallatë Caprese", "", "10.00", "sl_caprese"),
        ("Cezar Salata", "Caesar Salad", "Sallatë Cezar", "", "10.50", "sl_cezar"),
        ("Pileća Salata", "Chicken Salad", "Sallatë me Pule", "", "10.50", "sl_pileca"),
    ],
    # Grouped by type, in sequence, per the owner's request: all tortillas,
    # then all plata portions, then plain kebap, then all burgers, then the
    # rest — "when those finish, these begin."
    "hrana": [
        ("Tortilja Pileća", "Chicken Tortilla", "Tortilja Pule", "", "9.00", "food_extras"),
        ("Tortilja Juneća", "Beef Tortilla", "Tortilja Viçi", "", "9.00", "food_extras"),
        ("Tortilja Miješana", "Mixed Tortilla", "Tortilja Miks", "", "9.00", "food_extras"),
        ("Plata Juneća", "Beef Portion", "Plata Viçi", "", "14.00", "food_extras"),
        ("Plata Pileća", "Chicken Portion", "Plata Pule", "", "14.00", "food_extras"),
        ("Plata Miješana", "Mixed Portion", "Plata Miks", "", "14.00", "food_extras"),
        ("Kebab Juneći", "Beef Kebab", "Kebap Viçi", "", "9.00", "food_extras"),
        ("Kebab Pileći", "Chicken Kebab", "Kebap Pule", "", "9.00", "food_extras"),
        ("Kebab Miješani", "Mixed Kebab", "Kebap Miks", "", "9.00", "food_extras"),
        ("Hamburger", "Hamburger", "Hamburger", "", "9.00", "food_extras"),
        ("Double Burger", "Double Burger", "Double Burger", "", "15.00", "food_extras"),
        ("Cheeseburger", "Cheeseburger", "Cheeseburger", "", "9.50", "food_extras"),
        ("Double Cheeseburger", "Double Cheeseburger", "Double Cheeseburger", "", "16.00", "food_extras"),
        ("Chicken Burger", "Chicken Burger", "Chicken Burger", "", "10.00", "food_extras"),
        ("Nubeno Burger", "Nubeno Burger", "Nubeno Burger", "", "15.00", "food_extras"),
        ("Pileći medaljoni", "Chicken Nuggets", "Nagetsa Pule", "", "8.00", None),
        ("Pileći stek", "Chicken Steak", "Stek Pule", "", "12.00", None),
        ("Pileći stek (pohani)", "Chicken Steak (breaded)", "Stek Pule (i paniruar)", "", "13.00", None),
        ("Pileći prutići", "Chicken Fingers", "Gishta Pule", "", "13.00", None),
        ("Ćevapi", "Ćevapi", "Qebapa", "5x", "8.00", None),
        ("Ćevapi", "Ćevapi", "Qebapa", "10x", "13.00", None),
        ("Lignje", "Squids", "Kallamar", "", "15.00", None),
        ("Hot Dog", "Hot Dog", "Hot Dog", "", "7.00", None),
        ("Pomes frites", "French Fries", "Patate të Skuqura", "", "4.00", None),
        ("Onion Rings", "Onion Rings", "Unaza Qepe", "", "6.00", None),
        ("Mozzarella štapići", "Mozzarella Sticks", "Shkopinj Mocarele", "", "8.00", None),
        ("Lepinja", "Flatbread", "Lepinjë", "", "2.00", None),
        ("Razni dodaci", "Assorted Extras", "Shtesa të Ndryshme", "Mala porcija", "1.50", None),
        ("Razni dodaci", "Assorted Extras", "Shtesa të Ndryshme", "Velika porcija", "3.00", None),
    ],
    "alkoolike": [
        ("Točeno pivo", "Draft Beer", "Birrë me Fuçi", "0.30l", "3.00", None),
        ("Točeno pivo", "Draft Beer", "Birrë me Fuçi", "0.50l", "4.00", None),
        ("Karlovačko", "Karlovačko", "Karlovačko", "0.33l", "3.00", None),
        ("Karlovačko", "Karlovačko", "Karlovačko", "0.50l", "4.00", None),
        ("Karlovačko Crno", "Karlovačko Dark", "Karlovačko e Zezë", "0.50l", "4.00", None),
        ("Radler", "Radler", "Radler", "0.50l", "4.00", None),
        ("Ožujsko", "Ožujsko", "Ožujsko", "0.33l", "3.00", None),
        ("Ožujsko", "Ožujsko", "Ožujsko", "0.50l", "4.00", None),
        ("Somersby", "Somersby", "Somersby", "0.33l", "4.50", None),
        ("Heineken", "Heineken", "Heineken", "0.33l", "4.50", None),
        ("Vino", "Wine", "Verë", "0.10l", "2.00", None),
        ("Vino", "Wine", "Verë", "1.00l", "20.00", None),
        ("Gemišt", "Wine Spritzer", "Gemisht", "0.20l", "2.50", None),
        ("Pelinkovac", "Pelinkovac", "Pelinkovac", "0.03l", "2.50", None),
        ("Travarica", "Travarica", "Travarica", "0.03l", "2.50", None),
        ("Aperol Spritz", "Aperol Spritz", "Aperol Spritz", "", "6.00", None),
    ],
    "pije": [
        ("Coca Cola", "Coca Cola", "Coca Cola", "0.33l", "3.50", None),
        ("Fanta", "Fanta", "Fanta", "0.33l", "3.50", None),
        ("Schweppes", "Schweppes", "Schweppes", "0.33l", "3.50", None),
        ("Cockta", "Cockta", "Cockta", "0.33l", "3.50", None),
        ("Sprite", "Sprite", "Sprite", "0.275l", "3.50", None),
        ("Maraška", "Cherry Juice", "Lëng Qershie", "0.33l", "3.50", None),
        ("Negazirani sokovi (bočica)", "Still Juice (bottle)", "Lëng jo-gazuar (shishe)", "0.20l", "3.50", None),
        ("Cedevita", "Cedevita", "Cedevita", "0.20l", "3.50", None),
        ("Red Bull", "Red Bull", "Red Bull", "0.30l", "3.00", None),
        ("Limunada", "Lemonade", "Limonadë", "0.3l", "3.00", None),
        ("Limunada", "Lemonade", "Limonadë", "0.5l", "4.00", None),
        ("Ledeni Čaj", "Ice Tea", "Çaj i Ftohtë", "0.50l", "3.50", None),
        ("Jamnica", "Jamnica (sparkling)", "Jamnica", "0.3l", "2.50", None),
        ("Jamnica", "Jamnica (sparkling)", "Jamnica", "0.5l", "3.00", None),
        ("Jamnica", "Jamnica (still)", "Jamnica (pa gaz)", "1L", "5.50", None),
        ("Romerquelle", "Romerquelle", "Romerquelle", "0.50l", "2.50", None),
        ("Hidra", "Hidra", "Hidra", "0.50l", "3.50", None),
    ],
}


class Command(BaseCommand):
    help = "Seed the menu (categories, modifier groups, items) from the Nubeno price list."

    @transaction.atomic
    def handle(self, *args, **options):
        # Hide any category left over from an older menu structure so the
        # admin and API only ever show the current layout. Deactivate rather
        # than delete: a removed category (e.g. the old "Burgers"/"Kebab"
        # tabs folded back into "Hrana") still CASCADEs to its MenuItems,
        # which real historical OrderItems PROTECT-reference — see the
        # matching per-item deactivation below and menu/views.py, which
        # only ever returns active=True categories.
        keep_categories = {name_en for _, name_en, *_ in CATEGORIES.values()}
        Category.objects.exclude(name_en__in=keep_categories).update(active=False)
        keep_groups = {name_en for _, name_en, *_ in MODIFIER_GROUPS.values()}
        ModifierGroup.objects.exclude(name_en__in=keep_groups).delete()

        categories = {}
        for key, (name_hr, name_en, name_sq, group, order) in CATEGORIES.items():
            obj, _ = Category.objects.update_or_create(
                name_en=name_en,
                defaults=dict(
                    name_hr=name_hr, name_sq=name_sq, group=group, order=order,
                    active=True,
                ),
            )
            categories[key] = obj

        modifier_groups = {}
        for key, (name_hr, name_en, name_sq, options) in MODIFIER_GROUPS.items():
            group_obj, _ = ModifierGroup.objects.update_or_create(
                name_en=name_en, defaults=dict(name_hr=name_hr, name_sq=name_sq)
            )
            for i, (opt_hr, opt_en, opt_sq) in enumerate(options):
                ModifierOption.objects.update_or_create(
                    group=group_obj,
                    name_en=opt_en,
                    defaults=dict(name_hr=opt_hr, name_sq=opt_sq, order=i),
                )
            modifier_groups[key] = group_obj

        item_count = 0
        for cat_key, items in ITEMS.items():
            category = categories[cat_key]
            keep_item_keys = {(name_en, variant) for _, name_en, _, variant, *_ in items}
            for existing in MenuItem.objects.filter(category=category):
                if (existing.name_en, existing.variant_label) not in keep_item_keys:
                    # Past orders may PROTECT-reference this row (e.g. an item
                    # that moved to a different category, like burgers/kebabs
                    # out of the old catch-all "Hrana"). Deactivating instead
                    # of deleting keeps order history intact while hiding it
                    # from the active menu — see menu/serializers.py, which
                    # only ever returns active=True items.
                    existing.active = False
                    existing.save(update_fields=["active"])
            for i, (name_hr, name_en, name_sq, variant, price, mod_key) in enumerate(items):
                MenuItem.objects.update_or_create(
                    category=category,
                    name_en=name_en,
                    variant_label=variant,
                    defaults=dict(
                        name_hr=name_hr,
                        name_sq=name_sq,
                        price=price,
                        modifier_group=modifier_groups.get(mod_key) if mod_key else None,
                        order=i,
                        active=True,
                    ),
                )
                item_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(categories)} categories, {len(modifier_groups)} modifier groups, {item_count} menu items."
            )
        )
