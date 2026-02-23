from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Brand, Category, HeroSlider, Product, ProductImage, BlogPost, WebsiteLogo, Favicon
from .utils.image_utils import convert_to_webp
import os

def handle_image_conversion(instance, field_name):
    image_field = getattr(instance, field_name)
    if not image_field:
        return

    # Check if a new file is being uploaded or if the file has changed
    try:
        if instance.pk:
            old_instance = instance.__class__.objects.get(pk=instance.pk)
            old_file = getattr(old_instance, field_name)
            if old_file and old_file.name == image_field.name:
                return # File hasn't changed
    except instance.__class__.DoesNotExist:
        pass # New instance

    # Only convert if not already WebP
    if not image_field.name.lower().endswith('.webp'):
        webp_file = convert_to_webp(image_field)
        if webp_file:
            # Set the new file to the field
            getattr(instance, field_name).save(webp_file.name, webp_file, save=False)

@receiver(pre_save, sender=Brand)
def convert_brand_logo(sender, instance, **kwargs):
    handle_image_conversion(instance, 'logo')

@receiver(pre_save, sender=Category)
def convert_category_image(sender, instance, **kwargs):
    handle_image_conversion(instance, 'image')

@receiver(pre_save, sender=HeroSlider)
def convert_heroslider_image(sender, instance, **kwargs):
    handle_image_conversion(instance, 'image')

@receiver(pre_save, sender=Product)
def convert_product_main_image(sender, instance, **kwargs):
    handle_image_conversion(instance, 'main_image')

@receiver(pre_save, sender=ProductImage)
def convert_product_image(sender, instance, **kwargs):
    handle_image_conversion(instance, 'image')

@receiver(pre_save, sender=BlogPost)
def convert_blog_image(sender, instance, **kwargs):
    handle_image_conversion(instance, 'image')

@receiver(pre_save, sender=WebsiteLogo)
def convert_websitelogo_image(sender, instance, **kwargs):
    handle_image_conversion(instance, 'logo_image')

@receiver(pre_save, sender=Favicon)
def convert_favicon_image(sender, instance, **kwargs):
    handle_image_conversion(instance, 'icon')
