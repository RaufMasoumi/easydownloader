from django.contrib import admin
from .models import Content, AllowedExtractor
# Register your models here.


class ContentAdmin(admin.ModelAdmin):
    fields = [
        'url', 'celery_download_task_id',  'info_id', 'info_file_path', 'title', 'type', 'extension', 'resolution', 'frame_rate',
        'aspect_ratio', 'audio_bitrate', 'download_url', 'download_path', 'downloaded_successfully', 'expired', 'expiration_date'
    ]
    list_display = ['title', 'processed_at', 'downloaded_successfully', 'expired']


admin.site.register(Content, ContentAdmin)


class AllowedExtractorAdmin(admin.ModelAdmin):
    fields = ['name', 'regex', 'main_extractor', 'active']
    list_display = ['name', 'active']


admin.site.register(AllowedExtractor, AllowedExtractorAdmin)
