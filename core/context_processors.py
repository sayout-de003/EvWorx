from .models import WebsiteLogo, Favicon

def core_context(request):
    """
    Context processor to add common data to all templates.
    """
    try:
        active_logo = WebsiteLogo.objects.filter(is_active=True).first()
    except WebsiteLogo.DoesNotExist:
        active_logo = None
    
    favicon = Favicon.objects.first()
        
    return {
        'logo': active_logo,
        'favicon_obj': favicon,
    }
