from django.core.management.base import BaseCommand
from faker import Faker
import random

from products.models import Category, Product
from stores.models import Store, Inventory

fake = Faker()


class Command(BaseCommand):
    help = "Seed database with dummy data"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # Categories
        categories = []
        for _ in range(10):
            category = Category.objects.create(
                name=fake.word().capitalize()
            )
            categories.append(category)

        self.stdout.write("Categories created")

        # Products
        products = []
        for _ in range(1000):
            product = Product.objects.create(
                title=fake.word().capitalize(),
                description=fake.sentence(),
                price=random.uniform(10, 1000),
                category=random.choice(categories)
            )
            products.append(product)

        self.stdout.write("Products created")

        # Stores
        stores = []
        for _ in range(20):
            store = Store.objects.create(
                name=fake.company(),
                location=fake.city()
            )
            stores.append(store)

        self.stdout.write("Stores created")

        # Inventory
        for store in stores:
            sample_products = random.sample(products, 300)

            for product in sample_products:
                Inventory.objects.create(
                    store=store,
                    product=product,
                    quantity=random.randint(0, 100)
                )

        self.stdout.write(self.style.SUCCESS("Seeding completed successfully!"))