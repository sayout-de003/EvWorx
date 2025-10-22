from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django_ckeditor_5.views import upload_file

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Include all routes from core app
    path('ckeditor5/upload/', upload_file, name='ck_editor_5_upload_file'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
