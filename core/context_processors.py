from .models import Favicon

def favicon_context(request):
    favicon = Favicon.objects.first()
    return {'favicon_obj': favicon}
