import os
import sys
import argparse
import pandas as pd
import requests
import re
from io import BytesIO
from django.core.files import File
from django.utils.text import slugify
from decimal import Decimal, InvalidOperation

# Setup Django Environment
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evault.settings')
django.setup()

from core.models import Product, Brand, Category, Manufacturer

def clean_numeric(value):
    """Extracts numeric parts from strings like '5 SET' or '10.5%'"""
    if pd.isna(value) or value is None:
        return None
    # Extract numbers including decimal point
    matches = re.findall(r"[-+]?\d*\.\d+|\d+", str(value))
    return matches[0] if matches else None

def to_decimal(value, default=0):
    clean = clean_numeric(value)
    if clean is None:
        return Decimal(str(default))
    try:
        return Decimal(clean)
    except (InvalidOperation, ValueError):
        return Decimal(str(default))

def to_int(value, default=0):
    clean = clean_numeric(value)
    if clean is None:
        return int(default)
    try:
        return int(float(clean)) # float first handles cases like '5.0'
    except (ValueError, TypeError):
        return int(default)

def find_local_image(image_dir, part_number):
    """Finds a local image matching the part number (e.g., EVCK-001.jpg)"""
    if not image_dir or not part_number:
        return None
    
    extensions = ['.jpg', '.jpeg', '.png', '.webp']
    for ext in extensions:
        # Try exact match, then sanitized match
        file_path = os.path.join(image_dir, f"{part_number}{ext}")
        if os.path.exists(file_path):
            return file_path
        
        # Try sanitized name (no special chars)
        sanitized = re.sub(r'[^a-zA-Z0-9]', '', str(part_number))
        file_path = os.path.join(image_dir, f"{sanitized}{ext}")
        if os.path.exists(file_path):
            return file_path
    return None

def download_image(url):
    """Helper to download image from URL and return a Django File object"""
    if not url or pd.isna(url) or str(url).lower() == 'nan':
        return None
    
    url_str = str(url).strip()
    if not url_str.startswith('http'):
        # If it's a local file path (passed from import_data fallback)
        if os.path.exists(url_str):
            try:
                with open(url_str, 'rb') as f:
                    return File(BytesIO(f.read()), name=os.path.basename(url_str))
            except Exception as e:
                print(f"    [!] Failed to read local image {url_str}: {e}")
        return None

    try:
        response = requests.get(url_str, timeout=10)
        if response.status_code == 200:
            file_name = url_str.split("/")[-1].split("?")[0] # Basic filename extraction
            if not file_name:
                file_name = "product_image.jpg"
            return File(BytesIO(response.content), name=file_name)
    except Exception as e:
        print(f"    [!] Failed to download image {url_str}: {e}")
    return None

def import_data(source, image_dir=None):
    # Convert Google Sheet URL to Export CSV link if it is a URL
    if source.startswith('http'):
        if "edit" in source:
            source = source.split("edit")[0] + "export?format=csv"
        elif "pubhtml" in source:
            source = source.split("pubhtml")[0] + "pub?output=csv"
        
        print(f"Fetching data from: {source}")
    else:
        print(f"Loading data from local file: {source}")
    
    try:
        df = pd.read_csv(source)
    except Exception as e:
        if "401" in str(e):
            print("\nERROR: HTTP 401 Unauthorized.")
            print("If you are using a Google Sheet, make sure it is shared as 'Anyone with the link can view'.")
            print("Alternatively, download the CSV and run the script with: python import_products.py path/to/your/file.csv")
        else:
            print(f"\nERROR: Could not read source: {e}")
        return
    
    products_with_no_image = 0
    
    for index, row in df.iterrows():
        try:
            # 1. Handle Brand & Category
            brand_obj, _ = Brand.objects.get_or_create(name="Default Brand")
            cat_obj, _ = Category.objects.get_or_create(name="General")

            # 2. Map Columns to Model Fields
            product_title = str(row.get('Item', '')).strip()
            part_no = str(row.get('PART NO', '')).strip()
            
            if not product_title or product_title.lower() == 'nan':
                continue # Skip empty rows

            # Use update_or_create to prevent duplicates based on Part Number
            product, created = Product.objects.update_or_create(
                part_number=part_no,
                defaults={
                    'title': product_title,
                    'hsn_code': str(row.get('HSN CODE', '')),
                    'stock': to_int(row.get('QUANTITY')),
                    'gst_percentage': to_decimal(row.get('GST')),
                    'price': to_decimal(row.get('Dealer basic PRICE')),
                    'mrp': to_decimal(row.get('MRP')),
                    'brand': brand_obj,
                    'category': cat_obj,
                }
            )

            # 3. Handle Product Photo
            image_url = row.get('PHOTOS')
            img_file = None
            
            # Try URL first
            if image_url and not pd.isna(image_url) and str(image_url).startswith('http'):
                img_file = download_image(image_url)
            
            # Fallback to local image directory
            if not img_file and image_dir:
                local_path = find_local_image(image_dir, part_no)
                if local_path:
                    print(f"  [√] Found local image for {part_no}: {os.path.basename(local_path)}")
                    img_file = download_image(local_path)

            if img_file:
                # Always save if image found (allows updating missing images)
                product.main_image.save(img_file.name, img_file, save=False)
            elif not product.main_image:
                products_with_no_image += 1
                if not image_dir:
                    print(f"  [!] No photo URL found for {part_no}. Use --image-dir to provide local images.")
                else:
                    print(f"  [!] No image found for {part_no} in {image_dir}")
            
            product.save()
            print(f"{'[Created]' if created else '[Updated]'}: {product_title}")

        except Exception as e:
            print(f"Error at row {index}: {e}")

    if products_with_no_image > 0:
        print(f"\n--- IMPORT SUMMARY ---")
        print(f"Total products updated/created. however, {products_with_no_image} products have NO image.")
        print(f"NOTE: Google Sheets embedded images cannot be exported via CSV.")
        print(f"To fix this, upload your images to a folder (e.g., 'product_images/') and run:")
        print(f"python import_products.py --image-dir product_images/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import products from CSV or Google Sheet.")
    parser.add_argument("source", nargs="?", default="https://docs.google.com/spreadsheets/d/1rKBHhhgj4LLQCAhQ_ptjn8bM8Q2o8aU3/edit?usp=sharing&ouid=114467264217272608941&rtpof=true&sd=true", 
                        help="URL of the Google Sheet or path to a local CSV file.")
    parser.add_argument("--image-dir", help="Optional local directory to look for product images (named by Part Number).")
    
    args = parser.parse_args()
    import_data(args.source, image_dir=args.image_dir)