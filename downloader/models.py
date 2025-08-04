from django.db import models
from datetime import datetime, timedelta
from django.db.models import Q
import uuid
# Create your models here.


class ContentManager(models.Manager):
    def expired_contents(self):
        return self.filter(expiration_date__lte=datetime.now())
        # return self.filter(Q(expiration_date__lte=datetime.now()) || Q(expired=True))

    def valid_contents(self):
        return self.filter(expiration_date__gt=datetime.now())

    def downloaded_contents(self):
        return self.filter(downloaded_successfully=True)

    def downloaded_valid_contents(self):
        return self.filter(downloaded_successfully=True, expiration_date__gt=datetime.now())

    def downloaded_expired_contents(self):
        return self.filter(downloaded_successfully=True, expiration_date__lte=datetime.now())


class AllowedExtractorManager(models.Manager):
    def active_extractors(self):
        return self.filter(active=True)


class Content(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    info_id = models.CharField(max_length=300)
    info_file_path = models.FilePathField(path='info/')
    celery_download_task_id = models.CharField(max_length=300, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    title = models.CharField(max_length=300, blank=True, null=True)
    type = models.CharField(max_length=20, blank=True, null=True, default='audio')
    extension = models.CharField(max_length=20, blank=True, null=True, default='mp3')
    resolution = models.IntegerField(blank=True, null=True, default=360)
    frame_rate = models.IntegerField(blank=True, null=True)
    aspect_ratio = models.IntegerField(blank=True, null=True)
    audio_bitrate = models.IntegerField(blank=True, null=True, default=400)
    download_url = models.URLField(blank=True, null=True)
    download_path = models.FilePathField(path='temp/', blank=True, null=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(blank=True, null=True)
    downloaded_successfully = models.BooleanField(default=False)
    expired = models.BooleanField(blank=True, default=False)
    objects = ContentManager()

    class Meta:
        ordering = ['-processed_at', ]

    def __str__(self):
        return f'{self.pk} content'

    def save(self, **kwargs):
        # Setting expiration_date according to processed_at
        super().save(**kwargs)
        if self.processed_at and not self.expiration_date:
            self.expiration_date = self.processed_at + timedelta(hours=5)
            super().save(update_fields=['expiration_date', ])


class AllowedExtractor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=300)
    regex = models.CharField(max_length=300)
    main_extractor = models.ForeignKey('self', on_delete=models.CASCADE, related_name='detailed_extractors', blank=True, null=True)
    active = models.BooleanField(default=True, blank=True)
    objects = AllowedExtractorManager()

    def __str__(self):
        return f'{self.name} extractor'
