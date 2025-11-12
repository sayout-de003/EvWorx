from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from core.views import favicon_redirect
from django_ckeditor_5.views import upload_file

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('ckeditor5/upload/', upload_file, name='ck_editor_5_upload_file'),
    path('favicon.ico', favicon_redirect),  # dynamic redirect
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
