import os
import pandas as pd
import requests
from io import BytesIO
from django.core.files import File
from django.utils.text import slugify
from decimal import Decimal

# Setup Django Environment
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evault.settings')
django.setup()

from core.models import Product, Brand, Category, Manufacturer

def download_image(url):
    """Helper to download image from URL and return a Django File object"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            file_name = url.split("/")[-1].split("?")[0] # Basic filename extraction
            if not file_name:
                file_name = "product_image.jpg"
            return File(BytesIO(response.content), name=file_name)
    except Exception as e:
        print(f"Failed to download image {url}: {e}")
    return None

def import_data(csv_url):
    # Convert Google Sheet URL to Export CSV link
    if "edit?usp=sharing" in csv_url:
        csv_url = csv_url.replace("edit?usp=sharing", "export?format=csv")
    
    df = pd.read_csv(csv_url)
    
    for index, row in df.iterrows():
        try:
            # 1. Handle Brand & Category (Create if doesn't exist)
            # Assuming your sheet has columns for these. If not, we use defaults.
            brand_obj, _ = Brand.objects.get_or_create(name="Default Brand")
            cat_obj, _ = Category.objects.get_or_create(name="General")

            # 2. Map Excel Columns to Model Fields
            # Note: Ensure the string keys match your CSV headers exactly
            product_title = str(row['Item']).strip()
            
            # Use update_or_create to prevent duplicates based on Part Number
            product, created = Product.objects.update_or_create(
                part_number=str(row['PART NO']).strip(),
                defaults={
                    'title': product_title,
                    'hsn_code': str(row['HSN CODE']),
                    'stock': int(row['QUANTITY']),
                    'gst_percentage': Decimal(str(row['GST']).replace('%', '')),
                    'price': Decimal(str(row['Dealer basic PRICE'])),
                    'mrp': Decimal(str(row['MRP'])),
                    'brand': brand_obj,
                    'category': cat_obj,
                    # 'price' in your model is Dealer Basic, 'mrp' is MRP
                }
            )

            # 3. Handle Product Photo
            image_url = row.get('PHOTOS')
            if image_url and not product.main_image:
                img_file = download_image(image_url)
                if img_file:
                    product.main_image.save(img_file.name, img_file, save=False)
            
            product.save()
            print(f"{'Created' if created else 'Updated'}: {product_title}")

        except Exception as e:
            print(f"Error at row {index}: {e}")

if __name__ == "__main__":
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1rKBHhhgj4LLQCAhQ_ptjn8bM8Q2o8aU3/edit?usp=sharing"
    import_data(SHEET_URL)