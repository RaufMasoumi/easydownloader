from django.db import models
from datetime import timedelta
import uuid
# Create your models here.


class Content(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=300, blank=True, null=True)
    download_url = models.URLField(blank=True, null=True)
    download_path = models.FilePathField(path='temp/', blank=True, null=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.pk} content'

    def save(self, **kwargs):
        if self.processed_at and not self.expiration_date:
            self.expiration_date = self.processed_at + timedelta(hours=5)
            update_fields = kwargs.get('update_fields')
            if update_fields:
                kwargs['update_fields'] = {'expiration_date'}.union(update_fields)

        super().save(**kwargs)
