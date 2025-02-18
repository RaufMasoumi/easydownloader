from django.contrib import admin
from .models import Content, AllowedExtractor
# Register your models here.


class ContentAdmin(admin.ModelAdmin):
    fields = ['name', 'download_url', 'download_path']
    list_display = ['pk', 'processed_at', 'expiration_date']


admin.site.register(Content, ContentAdmin)


class AllowedExtractorAdmin(admin.ModelAdmin):
    fields = ['name', 'regex', 'main_extractor', 'active']
    list_display = ['name', 'active']

admin.site.register(AllowedExtractor, AllowedExtractorAdmin)