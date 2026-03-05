import os
import shutil
from io import BytesIO
from PIL import Image
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps
from django.db import models
from django.core.files.base import ContentFile

try:
    from rembg import remove
except ImportError:
    remove = None

class Command(BaseCommand):
    help = 'Removes background from product images using rembg and replaces it with white.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without saving changes',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of images to process (useful for testing)',
        )

    def handle(self, *args, **options):
        if remove is None:
            self.stdout.write(self.style.ERROR(
                "The 'rembg' library is not installed. Please run: pip install rembg pillow"
            ))
            return

        dry_run = options['dry_run']
        limit = options['limit']
        
        media_root = settings.MEDIA_ROOT
        backup_root = os.path.join(settings.BASE_DIR, 'backup_originals')

        if not dry_run and not os.path.exists(backup_root):
            os.makedirs(backup_root)
            self.stdout.write(self.style.SUCCESS(f'Created backup directory: {backup_root}'))

        # Targeted models and their image fields
        target_models = [
            ('core', 'Product', ['main_image']),
            ('core', 'ProductImage', ['image']),
        ]

        count = 0
        for app_label, model_name, fields in target_models:
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                self.stdout.write(self.style.WARNING(f"Model {app_label}.{model_name} not found."))
                continue

            self.stdout.write(f"Processing model: {model_name}")
            instances = model.objects.all()
            
            for instance in instances:
                if limit and count >= limit:
                    break
                
                updated = False
                for field_name in fields:
                    image_field = getattr(instance, field_name)
                    
                    if not image_field or not image_field.name:
                        continue

                    original_path = image_field.path
                    if not os.path.exists(original_path):
                        self.stdout.write(self.style.WARNING(f"File not found: {original_path}"))
                        continue

                    self.stdout.write(f"Processing {image_field.name}...")

                    try:
                        # 1. Backup original
                        relative_path = os.path.relpath(original_path, media_root)
                        backup_path = os.path.join(backup_root, relative_path)
                        backup_dir = os.path.dirname(backup_path)
                        
                        if not dry_run:
                            if not os.path.exists(backup_dir):
                                os.makedirs(backup_dir)
                            
                            # Use copy instead of move to keep original in place while processing
                            shutil.copy2(original_path, backup_path)

                        # 2. Remove background
                        with open(original_path, 'rb') as i:
                            input_data = i.read()
                            output_data = remove(input_data)

                        # 3. Apply white background
                        # output_data is RGBA (with transparency)
                        img = Image.open(BytesIO(output_data)).convert("RGBA")
                        
                        # Create white background
                        white_bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                        # Composite the image over white background
                        final_img = Image.alpha_composite(white_bg, img).convert("RGB")

                        # 4. Save processed image
                        if not dry_run:
                            # We'll save it back to the original path (maintaining format/extension if compatible)
                            # Or we can always save as PNG/JPEG. rembg output is usually PNG.
                            # Since user wants it for ecommerce, we might want to save as JPEG or WebP but 
                            # let's stick to the original extension but with white BG.
                            final_img.save(original_path)
                            updated = True
                            count += 1
                        else:
                            self.stdout.write(self.style.NOTICE(f"[Dry Run] Would process {image_field.name}"))
                            count += 1

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error processing {original_path}: {e}"))

                if updated and not dry_run:
                    # No need to change DB path if we overwrite the original file, 
                    # but if we wanted to change extension, we would need to update.
                    # For now, we overwrite the physical file.
                    pass

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'Dry run completed. {count} images would be processed.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Background removal completed for {count} images! Originals are backed up in backup_originals/'))
