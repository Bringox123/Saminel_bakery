from decimal import Decimal

from django.core.management.base import BaseCommand

from bakery.catalog_seed_data import (
    CATALOG_PRODUCTS,
    CATEGORY_NAMES,
    FEATURED_PRODUCT_NAMES,
)
from bakery.models import Category, Product


class Command(BaseCommand):
    help = 'Seed bakery categories and products from the catalog dataset.'

    def handle(self, *args, **options):
        featured_names = set(FEATURED_PRODUCT_NAMES)

        category_map: dict[str, Category] = {}
        categories_created = 0
        categories_existing = 0

        for name in CATEGORY_NAMES:
            category, created = Category.objects.get_or_create(name=name)
            category_map[name] = category
            if created:
                categories_created += 1
            else:
                categories_existing += 1

        products_created = 0
        products_updated = 0

        for item in CATALOG_PRODUCTS:
            product, created = Product.objects.update_or_create(
                name=item['name'],
                defaults={
                    'category': category_map[item['category']],
                    'description': item['description'],
                    'price': Decimal(item['price']),
                    'is_featured': item['name'] in featured_names,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                (
                    'Catalog seeding complete. '
                    f'Categories: +{categories_created} created, {categories_existing} existing. '
                    f'Products: +{products_created} created, {products_updated} updated.'
                )
            )
        )
