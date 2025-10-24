# myapp/management/commands/upload_products.py
import pandas as pd
from django.core.management.base import BaseCommand
from myapp.models import Product, Category  # adjust to your app

class Command(BaseCommand):
    help = 'Upload products directly from Google Sheet URL'

    def add_arguments(self, parser):
        parser.add_argument('sheet_url', type=str, help='Google Sheet shareable link')

    def handle(self, *args, **options):
        sheet_url = options['sheet_url']

        # Convert the Google Sheet URL to CSV export link
        if "edit" in sheet_url:
            csv_url = sheet_url.replace("/edit?usp=sharing", "/export?format=csv")
        else:
            self.stdout.write(self.style.ERROR("Invalid Google Sheet URL"))
            return

        try:
            df = pd.read_csv(csv_url)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching Google Sheet: {e}"))
            return

        for index, row in df.iterrows():
            title = row.get('title') or row.get('Title') or f"Product {index+1}"
            model_name = row.get('model') or row.get('Model') or "Default Model"
            content_model = row.get('content_model') or row.get('Content Model') or ""
            category_name = row.get('category') or row.get('Category') or "Uncategorized"
            price = row.get('price') or row.get('Price') or 0
            mrp = row.get('mrp') or row.get('MRP') or price

            # Get or create category
            category_obj, _ = Category.objects.get_or_create(name=category_name)

            # Create product
            product, created = Product.objects.get_or_create(
                title=title,
                defaults={
                    'model': model_name,
                    'content_model': content_model,
                    'category': category_obj,
                    'price': price,
                    'mrp': mrp,
                    'stock': 100,
                    'net_quantity': 100,
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Added product: {title}"))
            else:
                self.stdout.write(self.style.WARNING(f"Product already exists: {title}"))

        self.stdout.write(self.style.SUCCESS("All products uploaded successfully!"))
