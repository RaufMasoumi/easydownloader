from django.contrib import admin
from .models import Content, AllowedExtractor
# Register your models here.


class ContentAdmin(admin.ModelAdmin):
    fields = ['title', 'info_id', 'info_file_path', 'url', 'download_url', 'download_path', 'successful', 'expired', 'expiration_date']
    list_display = ['title', 'processed_at', 'successful', 'expired']


admin.site.register(Content, ContentAdmin)


class AllowedExtractorAdmin(admin.ModelAdmin):
    fields = ['name', 'regex', 'main_extractor', 'active']
    list_display = ['name', 'active']

admin.site.register(AllowedExtractor, AllowedExtractorAdmin)