# core/management/commands/populate_slugs.py
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from core.models import Product

class Command(BaseCommand):
    help = 'Populate slugs for products that do not have one'

    def handle(self, *args, **kwargs):
        products = Product.objects.filter(slug__isnull=True)
        for product in products:
            product.slug = slugify(product.title)
            original_slug = product.slug
            counter = 1
            while Product.objects.filter(slug=product.slug).exclude(id=product.id).exists():
                product.slug = f"{original_slug}-{counter}"
                counter += 1
            product.save()
            self.stdout.write(self.style.SUCCESS(f'Updated slug for product: {product.title} to {product.slug}'))