from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Read config from Django settings, the CELERY namespace means all celery-related
# configs must be prefixed with 'CELERY_'.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks from all installed apps
app.autodiscover_tasks()