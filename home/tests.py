from django.test import TestCase, override_settings
from django.shortcuts import reverse
from django.urls import resolve
from rest_framework import status
import os
from downloader.models import Content, AllowedExtractor
from downloader.tests import wait_until_file_is_being_processed_then_delete
from .views import HomeView
# Create your tests here.


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
)
class HomeViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.youtube_extractor = AllowedExtractor.objects.create(
            name='youtube',
            regex='^youtube',
            active=True,
        )
        cls.content_url = 'https://youtu.be/2PuFyjAs7JA?si=R6UuXVl-BPr-niXv'
        cls.path = reverse('home')

    def test_view_url(self):
        self.assertEqual(resolve(self.path).func.__name__, HomeView.as_view().__name__)

    def test_view_with_valid_data_get(self):
        data = {
            'url': self.content_url,
            'detail': 'audio mp3 320'
        }
        response = self.client.get(self.path, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Content.objects.count(), 1)
        content = Content.objects.first()
        self.assertContains(response, self.content_url)
        self.assertContains(response, content.title)
        self.assertNotContains(response, 'Not contains text')
        self.assertIsNotNone(content.celery_download_task_id)
        self.assertTemplateUsed(response, 'home/home.html')
        if os.path.exists(content.download_path):
            wait_until_file_is_being_processed_then_delete(content.download_path, tries=5)