import io
from PIL import Image
from django.core.files.base import ContentFile
import os

def convert_to_webp(image_field_file):
    """
    Converts a Django ImageField file to WebP format.
    """
    if not image_field_file:
        return None

    # Open the image using Pillow
    img = Image.open(image_field_file)
    
    # Create an in-memory byte stream
    output = io.BytesIO()
    
    # Save the image in WebP format to the byte stream
    img.save(output, format='WEBP', quality=80)
    output.seek(0)
    
    # Get the original filename and change extension
    original_name = os.path.basename(image_field_file.name)
    name_without_ext = os.path.splitext(original_name)[0]
    new_filename = f"{name_without_ext}.webp"
    
    # Return a Django ContentFile
    return ContentFile(output.read(), name=new_filename)
