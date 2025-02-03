from django.contrib import admin
from .models import Content
# Register your models here.


class ContentAdmin(admin.ModelAdmin):
    model = Content
    list_display = ['pk', 'processed_at', 'expiration_date']


admin.site.register(Content, ContentAdmin)
