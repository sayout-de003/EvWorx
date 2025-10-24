import pandas as pd
import requests
import os
from urllib.parse import urlparse
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from core.models import Product, Category, ProductImage

class Command(BaseCommand):
    help = 'Upload products directly from Google Sheet URL'

    def add_arguments(self, parser):
        parser.add_argument('sheet_url', type=str, help='Google Sheet shareable link')

    def clean_value(self, value, value_type='decimal'):
        """Helper function to clean numeric values from strings."""
        if value is None:
            return Decimal('0.0') if value_type == 'decimal' else 0
        
        str_value = str(value).strip()
        # Remove common currency/symbols and text
        numeric_part = str_value.replace('₹', '').replace(',', '')
        numeric_part = numeric_part.split('/')[0].split(' ')[0].strip()
        
        try:
            if value_type == 'decimal':
                return Decimal(numeric_part)
            elif value_type == 'int':
                # Convert to float first in case it's "10.0"
                return int(float(numeric_part))
        except (ValueError, InvalidOperation, TypeError):
            self.stdout.write(self.style.WARNING(f"Could not parse {value_type} from '{value}'. Defaulting to 0."))
            return Decimal('0.0') if value_type == 'decimal' else 0

    def get_net_quantity(self, value):
        """Helper function to extract unit from price string like '₹99.9 / PCS'."""
        if value is None:
            return None
        str_value = str(value).strip()
        if '/' in str_value:
            parts = str_value.split('/')
            if len(parts) > 1:
                return parts[1].strip()  # e.g., "PCS"
        return None  # Let model default (blank=True, null=True) handle it

    def download_and_save_image(self, product, image_url, is_main=False, index=0):
        """Downloads an image from a URL and saves it to the product."""
        if not image_url or not image_url.startswith('http'):
            self.stdout.write(self.style.WARNING(f"Invalid or empty image URL for {product.title}: {image_url}"))
            return

        try:
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

            # Get original extension or default to .jpg
            path = urlparse(image_url).path
            ext = os.path.splitext(path)[1]
            if not ext:
                ext = '.jpg'
            
            # Create a unique, descriptive name
            filename = f"{product.slug}-{index}{ext}"
            image_content = ContentFile(response.content)

            if is_main:
                # Save to main_image field
                product.main_image.save(filename, image_content, save=True)
                self.stdout.write(self.style.SUCCESS(f"Saved main image for {product.title}"))
            else:
                # Create and save to ProductImage model
                pi = ProductImage(product=product)
                pi.image.save(filename, image_content, save=True)
                self.stdout.write(self.style.SUCCESS(f"Saved additional image for {product.title}"))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Error downloading image {image_url} for {product.title}: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error saving image {image_url} for {product.title}: {e}"))


    def handle(self, *args, **options):
        sheet_url = options['sheet_url']

        # Convert the Google Sheet URL to CSV export link
        if "/edit" in sheet_url:
            csv_url = sheet_url.split('/edit')[0] + "/export?format=csv"
        else:
            self.stdout.write(self.style.ERROR("Invalid Google Sheet URL format. Use the 'share' link."))
            return

        try:
            # Read all data as strings to prevent pandas from auto-converting
            df = pd.read_csv(csv_url, dtype=str).fillna('')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching Google Sheet: {e}"))
            return

        for index, row in df.iterrows():
            # --- 1. Get data and handle column name variations ---
            title = row.get('Title') or row.get('title')
            if not title:
                self.stdout.write(self.style.WARNING(f"Skipping row {index+2}: No title found."))
                continue

            category_name = row.get('Category') or row.get('category') or "Uncategorized"
            
            raw_price = row.get('Price') or row.get('price')
            raw_mrp = row.get('MRP') or row.get('mrp')
            raw_stock = row.get('Stock') or row.get('stock')
            raw_moq = row.get('Minimum Quantity') or row.get('minimum quantity') or row.get('moq')
            
            description = row.get('Content') or row.get('content') or row.get('description') or ""
            image_urls_str = row.get('Images') or row.get('images') or ""
            
            # --- 2. Clean and convert data ---
            price = self.clean_value(raw_price, 'decimal')
            mrp = self.clean_value(raw_mrp, 'decimal')
            if mrp == Decimal('0.0'):
                mrp = price  # Default MRP to price if not specified
                
            stock = self.clean_value(raw_stock, 'int')
            moq = self.clean_value(raw_moq, 'int')
            if moq == 0:
                moq = 5 # Use model default if sheet is 0 or empty

            net_quantity = self.get_net_quantity(raw_price) # Try to get 'PCS' etc.

            # --- 3. Get or create Category ---
            category_obj, _ = Category.objects.get_or_create(name=category_name)

            # --- 4. Create or update Product ---
            # Use update_or_create to update existing products based on title
            product, created = Product.objects.update_or_create(
                title=title,
                defaults={
                    'category': category_obj,
                    'price': price,
                    'mrp': mrp,
                    'stock': stock,
                    'moq': moq,
                    'description': description,
                    'net_quantity': net_quantity,
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created new product: {title}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated existing product: {title}"))

            # --- 5. Handle Image Downloads ---
            if image_urls_str:
                # Clear existing images before adding new ones
                if not created:
                    if product.main_image:
                        product.main_image.delete(save=False) # Delete old main image
                    ProductImage.objects.filter(product=product).delete() # Delete old additional images
                    self.stdout.write(self.style.NOTICE(f"Cleared old images for {title}"))


                image_urls = [url.strip() for url in image_urls_str.split(',') if url.strip().startswith('http')]
                
                if image_urls:
                    # Download and save main image (first one)
                    self.download_and_save_image(product, image_urls[0], is_main=True, index=0)
                    
                    # Download and save remaining images
                    for i, image_url in enumerate(image_urls[1:], start=1):
                        self.download_and_save_image(product, image_url, is_main=False, index=i)

        self.stdout.write(self.style.SUCCESS("All products processed successfully!"))