import os
import pandas as pd
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from openpyxl import load_workbook
from core.models import Product, Category, Brand

class Command(BaseCommand):
    help = 'Import products and images from Excel'

    def handle(self, *args, **kwargs):
        excel_path = '/Users/sayantande/Downloads/spare.xlsx'
        media_path = '/Users/sayantande/ev/evault/media/products'
        os.makedirs(media_path, exist_ok=True)

        # Read Excel rows (skip 2 heading rows)
        try:
            df = pd.read_excel(excel_path, skiprows=2)
            self.stdout.write(">>> Excel Columns: " + str(df.columns.tolist()))
        except Exception as e:
            self.stderr.write(f"❌ Failed to read Excel file: {e}")
            return

        # Rename columns
        df.rename(columns={
            'PART NO': 'part_number',
            'Item': 'title',
            'Dealer Price\n( Iincluding GST)': 'dealer_price',
            'PHOTOS': 'photo'
        }, inplace=True)

        required_columns = ['part_number', 'title', 'dealer_price']
        for col in required_columns:
            if col not in df.columns:
                self.stderr.write(f"❌ Missing required column: {col}")
                return

        # Load Excel workbook to get embedded images
        wb = load_workbook(excel_path)
        ws = wb.active

        # Map row numbers to image objects
        row_images = {}
        for img in ws._images:
            anchor_row = img.anchor._from.row
            row_images[anchor_row] = img

        default_brand, _ = Brand.objects.get_or_create(name='Generic')

        created, updated, skipped = 0, 0, 0

        for idx, row in df.iterrows():
            excel_row = idx + 3  # Excel index starts from row 3

            part_number = str(row.get('part_number')).strip() if pd.notna(row.get('part_number')) else None
            title = str(row.get('title')).strip() if pd.notna(row.get('title')) else None
            price = float(row.get('dealer_price')) if pd.notna(row.get('dealer_price')) else 0.0

            if not part_number or not title:
                skipped += 1
                continue

            # Derive category from first word in title
            category_name = title.split()[0].capitalize()
            category, _ = Category.objects.get_or_create(name=category_name)

            # Create or update Product
            product, created_flag = Product.objects.update_or_create(
                part_number=part_number,
                defaults={
                    'title': title,
                    'price': price,
                    'brand': default_brand,
                    'category': category,
                    'stock': 10,
                }
            )

            # Assign embedded image (if exists)
            if excel_row in row_images:
                img = row_images[excel_row]
                img_bytes = img._data()
                image_name = f"{part_number}.jpg"
                image_path = os.path.join(media_path, image_name)

                with open(image_path, 'wb') as f:
                    f.write(img_bytes)

                product.image.save(image_name, ContentFile(img_bytes), save=True)
                self.stdout.write(f"🖼️  Image saved and assigned for {part_number}")
            else:
                self.stdout.write(f"⚠️  No image found for {part_number}")

            if created_flag:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Done: {created} created, {updated} updated, {skipped} skipped."
        ))
