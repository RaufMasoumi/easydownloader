from django.test import TestCase, override_settings
from django.shortcuts import reverse
from django.urls import resolve
from django.http import FileResponse
from rest_framework.test import APITestCase
from rest_framework import status
from celery.result import AsyncResult
import os
from downloader.main_downloader import MainDownloader, CustomYoutubeDL
from downloader.models import AllowedExtractor, Content
from downloader.tests import wait_until_file_is_being_processed_then_delete
from .views import GetContentInfoAPIView, DownloadContentAPIView


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_STORE_EAGER_RESULT=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
)
class GetContentInfoAPIViewTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.youtube_extractor = AllowedExtractor.objects.create(
            name='youtube',
            regex='^youtube',
            active=True,
        )
        cls.content_url = 'https://youtu.be/2PuFyjAs7JA?si=R6UuXVl-BPr-niXv'
        cls.main_downloader_obj = MainDownloader(
            url=cls.content_url,
            detail={'type': 'audio', 'audio_bitrate': 320, 'extension': 'mp3'},
        )
        with CustomYoutubeDL(cls.main_downloader_obj.options) as ytdl_obj:
            cls.info = cls.main_downloader_obj.extract_info(ytdl_obj)
        cls.path = reverse('get-content-info-api')

    def test_view_url(self):
        self.assertEqual(resolve(self.path).func.__name__, GetContentInfoAPIView.as_view().__name__)

    def test_view_with_valid_data_get(self):
        data = {
            'url': self.content_url,
            'type': 'audio',
            'audio_bitrate': 320,
            'extension': 'mp3',
        }
        response = self.client.get(self.path, data=data)
        if Content.objects.filter(pk=response.data.get('pk')).exists():
            content = Content.objects.get(pk=response.data.get('pk'))
        else:
            self.fail('The content is not created')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # response.data?
        self.assertContains(response, self.content_url)
        self.assertContains(response, self.info.get('title', None))
        self.assertNotContains(response, 'Not contains text')
        self.assertIsNotNone(content.celery_download_task_id)
        download_task_result = AsyncResult(content.celery_download_task_id)
        download_task_result.get()
        content.refresh_from_db()
        if os.path.exists(content.download_path):
            os.remove(content.download_path)

    def test_view_with_invalid_data_get(self):
        data1 = {
            'url': 'invalid url',
        }
        response1 = self.client.get(self.path, data=data1)
        self.assertEqual(response1.status_code, status.HTTP_400_BAD_REQUEST)
        data2 = {
            'url': self.content_url,
            'type': 'invalid type',
        }
        response2 = self.client.get(self.path, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_view_with_valid_data_post(self):
        data = {
            'url': self.content_url,
            'type': 'audio',
            'audio_bitrate': 320,
            'extension': 'mp3',
        }
        response = self.client.post(self.path, data=data)
        if Content.objects.filter(pk=response.data.get('pk')).exists():
            content = Content.objects.get(pk=response.data.get('pk'))
        else:
            self.fail('The content is not created')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.content_url)
        self.assertContains(response, self.info.get('title', None))
        self.assertNotContains(response, 'Not contains text')
        self.assertIsNotNone(content.celery_download_task_id)
        download_task_result = AsyncResult(content.celery_download_task_id)
        download_task_result.get()
        content.refresh_from_db()
        if os.path.exists(content.download_path):
            os.remove(content.download_path)

    def test_view_with_invalid_data_post(self):
        data1 = {
            'url': 'invalid url',
        }
        response1 = self.client.post(self.path, data=data1)
        self.assertEqual(response1.status_code, status.HTTP_400_BAD_REQUEST)
        data2 = {
            'url': self.content_url,
            'type': 'invalid type',
        }
        response2 = self.client.get(self.path, data=data2)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_STORE_EAGER_RESULT=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
)
class DownloadContentAPIViewTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.youtube_extractor = AllowedExtractor.objects.create(
            name='youtube',
            regex='^youtube',
            active=True,
        )
        cls.content_url = 'https://youtu.be/2PuFyjAs7JA?si=R6UuXVl-BPr-niXv'
        cls.main_downloader_obj = MainDownloader(
            url=cls.content_url,
            detail={'type': 'audio', 'audio_bitrate': 320, 'extension': 'mp3'},
        )
        with CustomYoutubeDL(cls.main_downloader_obj.options) as ytdl_obj:
            cls.info = cls.main_downloader_obj.extract_info(ytdl_obj)

    def setUp(self):
        self.content = Content.objects.create(
            url=self.content_url,
            info_id=self.info['id'],
            info_file_path=self.info['info_file_path'],
            type='audio',
            audio_bitrate=320,
            extension='mp3',
        )
        self.path = reverse('download-content-api', kwargs={'pk': self.content.pk})

    def test_view_url(self):
        self.assertEqual(resolve(self.path).func.__name__, DownloadContentAPIView.as_view().__name__)

    def test_view_separately_get(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.content.refresh_from_db()
        self.assertTrue(self.content.downloaded_successfully)
        self.assertIsNotNone(self.content.download_path)
        self.assertTrue(os.path.exists(self.content.download_path))
        self.assertTrue(os.path.isfile(self.content.download_path))
        self.assertIsInstance(response, FileResponse)
        self.assertIn('attachment;', response.get('Content-Disposition', None))
        self.assertEqual(response['Content-Type'], 'audio/mpeg')
        wait_until_file_is_being_processed_then_delete(self.content.download_path, tries=5)


    def test_view_separately_post(self):
        response = self.client.post(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.content.refresh_from_db()
        self.assertTrue(self.content.downloaded_successfully)
        self.assertIsNotNone(self.content.download_path)
        self.assertTrue(os.path.exists(self.content.download_path))
        self.assertTrue(os.path.isfile(self.content.download_path))
        self.assertIsInstance(response, FileResponse)
        self.assertIn('attachment;', response.get('Content-Disposition', None))
        self.assertEqual(response['Content-Type'], 'audio/mpeg')
        wait_until_file_is_being_processed_then_delete(self.content.download_path, tries=5)


    def test_view_with_get_content_info_api_view(self):
        data = {
            'url': self.content_url,
            'type': 'audio',
            'audio_bitrate': 320,
            'extension': 'mp3',
        }
        get_info_response = self.client.get(reverse('get-content-info-api'), data=data)
        if Content.objects.filter(pk=get_info_response.data.get('pk')).exists():
            content = Content.objects.get(pk=get_info_response.data.get('pk'))
        else:
            self.fail('The content is not created')
        download_content_response = self.client.get(reverse('download-content-api', kwargs={'pk': content.pk}))
        content.refresh_from_db()
        self.assertEqual(download_content_response.status_code, status.HTTP_200_OK)
        self.assertTrue(content.downloaded_successfully)
        self.assertIsNotNone(content.download_path)
        self.assertTrue(os.path.exists(content.download_path))
        self.assertTrue(os.path.isfile(content.download_path))
        self.assertIsInstance(download_content_response, FileResponse)
        self.assertIn('attachment;', download_content_response.get('Content-Disposition', None))
        self.assertEqual(download_content_response['Content-Type'], 'audio/mpeg')
        wait_until_file_is_being_processed_then_delete(content.download_path, tries=5)

