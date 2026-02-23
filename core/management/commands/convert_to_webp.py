import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps
from django.db import models
from core.utils.image_utils import convert_to_webp
from django.core.files.base import ContentFile

class Command(BaseCommand):
    help = 'Converts all existing images in the media directory to WebP format and updates database references.'

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        backup_root = os.path.join(settings.BASE_DIR, 'backup_originals')

        if not os.path.exists(backup_root):
            os.makedirs(backup_root)
            self.stdout.write(self.style.SUCCESS(f'Created backup directory: {backup_root}'))

        # Get all models
        all_models = apps.get_models()
        self.stdout.write(f"Scanning {len(all_models)} models...")

        for model in all_models:
            # Find models with ImageField
            image_fields = [f for f in model._meta.fields if isinstance(f, models.ImageField)]
            if not image_fields:
                continue

            self.stdout.write(f"Processing model: {model.__name__}")
            
            instances = model.objects.all()
            for instance in instances:
                updated = False
                for field in image_fields:
                    image_field_file = getattr(instance, field.name)
                    
                    if not image_field_file or not image_field_file.name:
                        continue
                    
                    if image_field_file.name.lower().endswith('.webp'):
                        continue

                    original_path = image_field_file.path
                    if not os.path.exists(original_path):
                        self.stdout.write(self.style.WARNING(f"File not found: {original_path}"))
                        continue

                    self.stdout.write(f"Converting {image_field_file.name}...")

                    try:
                        # Convert to WebP
                        webp_content_file = convert_to_webp(image_field_file)
                        
                        if webp_content_file:
                            # Save the new file
                            # Django will handle the path relative to upload_to
                            new_name = webp_content_file.name
                            image_field_file.save(new_name, webp_content_file, save=False)
                            
                            # Backup original
                            relative_path = os.path.relpath(original_path, media_root)
                            backup_path = os.path.join(backup_root, relative_path)
                            backup_dir = os.path.dirname(backup_path)
                            
                            if not os.path.exists(backup_dir):
                                os.makedirs(backup_dir)
                            
                            shutil.move(original_path, backup_path)
                            updated = True
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error converting {original_path}: {e}"))

                if updated:
                    instance.save()

        self.stdout.write(self.style.SUCCESS('Bulk conversion completed! Originals are backed up in backup_originals/'))
