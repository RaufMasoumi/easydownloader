from django.db import models
from datetime import timedelta
import uuid
# Create your models here.


class AllowedExtractorManager(models.Manager):
    def active_extractors(self):
        return self.filter(active=True)


class Content(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    info_id = models.CharField(max_length=300)
    info_file_path = models.FilePathField(path='info/')
    url = models.URLField(blank=True, null=True)
    title = models.CharField(max_length=300, blank=True, null=True)
    download_url = models.URLField(blank=True, null=True)
    download_path = models.FilePathField(path='temp/', blank=True, null=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(blank=True, null=True)
    successful = models.BooleanField(default=False)
    expired = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return f'{self.pk} content'

    def save(self, **kwargs):
        # Setting expiration_date according to processed_at
        super().save(**kwargs)
        if self.processed_at and not self.expiration_date:
            self.expiration_date = self.processed_at + timedelta(hours=5)
            update_fields = kwargs.get('update_fields')
            if update_fields:
                kwargs['update_fields'] = {'expiration_date'}.union(update_fields)
        super().save()


class AllowedExtractor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=300)
    regex = models.CharField(max_length=300)
    main_extractor = models.ForeignKey('self', on_delete=models.CASCADE, related_name='detailed_extractors', blank=True, null=True)
    active = models.BooleanField(default=True, blank=True)
    objects = AllowedExtractorManager()

    def __str__(self):
        return f'{self.name} extractor'