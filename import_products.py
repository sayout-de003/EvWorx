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
    use_excel = False
    # Convert Google Sheet URL to Export link
    # We prefer Excel (.xlsx) because it preserves embedded images
    if source.startswith('http'):
        if "edit" in source or "usp=sharing" in source:
            source = source.split("edit")[0].split("?")[0] + "export?format=xlsx"
            use_excel = True
        elif "pubhtml" in source:
            source = source.split("pubhtml")[0] + "pub?output=xlsx"
            use_excel = True
        
        print(f"Fetching data from: {source}")
    elif source.lower().endswith('.xlsx'):
        use_excel = True
        print(f"Loading data from local Excel file: {source}")
    else:
        print(f"Loading data from local CSV file: {source}")
    
    # Pre-validation for image directory
    if image_dir:
        if not os.path.exists(image_dir):
            print(f"\nWARNING: Directory '{image_dir}' NOT FOUND.")
            image_dir = None
        else:
            files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            if files:
                print(f"\n[OK] Found {len(files)} potential images in '{image_dir}'")

    image_map = {} # Maps row index to image file data
    
    try:
        if use_excel:
            import openpyxl
            from openpyxl.drawing.image import Image as OpenpyxlImage
            
            # Download to memory if it's a URL
            if source.startswith('http'):
                response = requests.get(source)
                file_content = BytesIO(response.content)
            else:
                file_content = source
                
            wb = openpyxl.load_workbook(file_content, data_only=True)
            ws = wb.active
            
            # Extract images and their anchors
            print(f"Extracting embedded images from Excel...")
            for image in ws._images:
                # anchor._from.row is 0-indexed row
                row_idx = image.anchor._from.row
                image_map[row_idx] = image._data()
            
            # Convert worksheet to DataFrame
            data = ws.values
            cols = next(data)
            df = pd.DataFrame(data, columns=cols)
            # Adjust row index for image_map because we skipped the header row
            # If the image was on row 2 (index 1), and header was row 1 (index 0), 
            # now row 2 is index 0 in our new df.
            image_map = {k - 1: v for k, v in image_map.items()}
            
        else:
            df = pd.read_csv(source)
            
    except Exception as e:
        print(f"\nERROR: Could not read source: {e}")
        return
    
    products_with_no_image = 0
    images_matched = 0
    
    for index, row in df.iterrows():
        try:
            # 1. Handle Brand & Category
            brand_obj, _ = Brand.objects.get_or_create(name="Default Brand")
            cat_obj, _ = Category.objects.get_or_create(name="General")

            # 2. Map Columns to Model Fields
            product_title = str(row.get('Item', '')).strip()
            part_no = str(row.get('PART NO', '')).strip()
            
            # Skip empty rows or header rows that slipped through
            if not product_title or product_title.lower() in ['nan', 'none', 'item']:
                continue 
            if part_no.lower() in ['part no', 'nan', 'none']:
                continue

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
            
            # Priority 1: Direct URL from sheet (if any)
            if image_url and not pd.isna(image_url) and str(image_url).startswith('http'):
                img_file = download_image(image_url)
            
            # Priority 2: Extracted from Excel row
            if not img_file and index in image_map:
                try:
                    img_data = image_map[index]
                    # We don't know the extension for sure from binary data easily without extra libs, 
                    # but usually it's png or jpg in Excel.
                    img_file = File(BytesIO(img_data), name=f"{part_no}.png")
                    print(f"  [√] Extracted embedded image for {part_no}")
                    images_matched += 1
                except Exception as e:
                    print(f"    [!] Failed to process extracted image for {part_no}: {e}")

            # Priority 3: Fallback to local image directory
            if not img_file and image_dir:
                local_path = find_local_image(image_dir, part_no)
                if local_path:
                    print(f"  [√] Found local image for {part_no}: {os.path.basename(local_path)}")
                    img_file = download_image(local_path)
                    images_matched += 1

            if img_file:
                product.main_image.save(img_file.name, img_file, save=False)
            elif not product.main_image:
                products_with_no_image += 1
                if not use_excel and not image_dir:
                    print(f"  [!] No photo URL for {part_no}. Hint: Use a Google Sheet URL or provided --image-dir.")
            
            product.save()
            print(f"{'[Created]' if created else '[Updated]'}: {product_title}")

        except Exception as e:
            print(f"Error at row {index}: {e}")

    print(f"\n--- IMPORT SUMMARY ---")
    print(f"Total Rows Processed: {len(df)}")
    print(f"Images Successfully Matched/Extracted: {images_matched}")
    print(f"Products Still Missing Image: {products_with_no_image}")
    
    if products_with_no_image > 0:
        print(f"\n[!] NOTE: {products_with_no_image} products still have NO image.")
        if not use_excel:
            print(f"TIP: Use the direct Google Sheet URL instead of a CSV file to extract images automatically!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import products from Excel or Google Sheet.")
    parser.add_argument("source", nargs="?", default="https://docs.google.com/spreadsheets/d/1rKBHhhgj4LLQCAhQ_ptjn8bM8Q2o8aU3/edit?usp=sharing", 
                        help="URL of the Google Sheet or path to a local XLSX/CSV file.")
    parser.add_argument("--image-dir", help="Optional local directory to look for product images (named by Part Number).")
    
    args = parser.parse_args()
    import_data(args.source, image_dir=args.image_dir)