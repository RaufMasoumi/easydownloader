from django.test import TestCase, override_settings
from django.shortcuts import reverse
from django.urls import resolve
from django.http import FileResponse
from rest_framework import status
from celery.result import AsyncResult
from datetime import timedelta
import json
import os
import time
from .main_downloader import MainDownloader, CustomYoutubeDL, DownloadProcessError
from .downloaders import BaseDownloader, YoutubeDownloader
from .models import Content, AllowedExtractor
from .tasks import async_extract_info, async_process_url, async_download_content
from .views import DownloadContentView
# Create your tests here.


class ContentTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.content = Content.objects.create(
            info_id='2PuFyjAs7JA',
            info_file_path='info/info-2PuFyjAs7JA.json',
            title='test content',
            type='audio',
            extension='mp3',
        )
        cls.content2 = Content.objects.create(
            info_id='2PuFyjAs7JA',
            info_file_path='info/info-2PuFyjAs7JA.json',
            title='test content2',
            type='audio',
            extension='mp3',
            audio_bitrate=320,
        )

    def test_model_creation(self):
        self.assertEqual(Content.objects.count(), 2)
        self.assertTrue(Content.objects.filter(title='test content').exists())
        self.assertEqual(Content.objects.get(pk=self.content.pk).title, 'test content')
        self.assertEqual(Content.objects.get(pk=self.content2.pk).audio_bitrate, 320)

    def test_expiration_date_setting(self):
        self.assertFalse(self.content.expired)
        self.assertEqual(self.content.expiration_date, self.content.processed_at + timedelta(hours=5))

    def test_model_manager(self):
        self.assertEqual(Content.objects.expired_contents().count(), 0)
        self.assertEqual(Content.objects.valid_contents().count(), 2)
        self.assertEqual(Content.objects.downloaded_contents().count(), 0)
        self.assertEqual(Content.objects.downloaded_valid_contents().count(), 0)
        self.assertEqual(Content.objects.downloaded_expired_contents().count(), 0)


class AllowedExtractorTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.allowed_extractor = AllowedExtractor.objects.create(
            name='testextractor',
            regex='^testextractor',
            active=True,
        )
        cls.allowed_extractor2 = AllowedExtractor.objects.create(
            name='testextractor2',
            regex='^testextractor2',
            active=False,
        )

    def test_model_creation(self):
        self.assertEqual(AllowedExtractor.objects.count(), 2)
        self.assertTrue(AllowedExtractor.objects.filter(name='testextractor').exists())
        self.assertEqual(AllowedExtractor.objects.get(pk=self.allowed_extractor.pk).regex, '^testextractor')

    def test_model_manager(self):
        self.assertEqual(AllowedExtractor.objects.active_extractors().count(), 1)


class MainDownloaderTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.youtube_extractor = AllowedExtractor.objects.create(
            name='youtube',
            regex='^youtube',
            active=True,
        )
        cls.instagram_extractor = AllowedExtractor.objects.create(
            name='instagram',
            regex='^instagram',
            active=False,
        )
        cls.content_url = 'https://youtu.be/2PuFyjAs7JA?si=R6UuXVl-BPr-niXv'
        with CustomYoutubeDL() as ytdl_obj:
            cls.info = ytdl_obj.extract_info(cls.content_url, download=False)
            cls.info['info_file_path'] = f'info/info-{cls.info['id']}.json'

    def setUp(self):
        self.main_downloader_obj = MainDownloader(
            url=self.content_url,
            detail={'type': 'audio', 'audio_bitrate': 320, 'extension': 'mp3'},
        )

    def test_default_options(self):
        """
            Tests MainDownloader default_options property that will be updated with given options argument.
        """
        self.assertDictEqual(self.main_downloader_obj.options, self.main_downloader_obj.default_options)
        self.assertEqual(self.main_downloader_obj.default_options.get('format', None), 'bestaudio[ext=mp3]/bestaudio/best')
        self.assertEqual(self.main_downloader_obj.default_options.get('outtmpl', None), 'temp/%(title)s.%(ext)s')
        self.assertListEqual(self.main_downloader_obj.default_options.get('allowed_extractors', list()), [self.youtube_extractor.regex, ])

    def test_info_extraction_without_info_without_info_file(self):
        """
            Tests extract_info method of MainDownloader in the situation that no info and no info_file_path was given.
            It should extract info using extract_info method of ytdl_obj and write info file.
            It should set info and info_file_path properties of main_downloader_obj.
        """
        with CustomYoutubeDL(self.main_downloader_obj.options) as ytdl_obj:
            info = self.main_downloader_obj.extract_info(ytdl_obj)
            self.assertIsInstance(info, dict)
            self.assertEqual(info.get('original_url', None), self.content_url)
            self.assertEqual(info['id'], self.main_downloader_obj.info['id'])
            self.assertEqual(self.main_downloader_obj.info_file_path, f'info/info-{info['id']}.json')
            self.assertEqual(self.main_downloader_obj.info_file_path, info['info_file_path'])
            self.assertTrue(os.path.exists(self.main_downloader_obj.info_file_path))
            self.assertTrue(os.path.isfile(self.main_downloader_obj.info_file_path))
            with open(self.main_downloader_obj.info_file_path, 'r') as info_file:
                self.assertEqual(info['id'], json.load(info_file)['id'])

    def test_info_extraction_with_info_without_info_file(self):
        """
            Tests extract_info method of MainDownloader in the situation that info was given but no info_file_path was given.
            It should write info file and set info_file_path.
        """
        self.main_downloader_obj.info = getattr(self, 'info', dict())
        with CustomYoutubeDL(self.main_downloader_obj.options) as ytdl_obj:
            self.main_downloader_obj.extract_info(ytdl_obj)
            self.assertEqual(self.main_downloader_obj.info_file_path, f'info/info-{self.info['id']}.json')
            self.assertTrue(os.path.exists(self.main_downloader_obj.info_file_path))
            self.assertTrue(os.path.isfile(self.main_downloader_obj.info_file_path))
            with open(self.main_downloader_obj.info_file_path, 'r') as info_file:
                self.assertEqual(self.info['id'], json.load(info_file)['id'])

    def test_info_extraction_with_similar_content(self):
        """
            Tests extract_info method of MainDownloader in the situation that info was not given but there is a similar Content entry.
            It should collect info and set info and info_file_path properties of main_downloader_obj.
        """
        similar_content = Content.objects.create(
            info_id=self.info['id'],
            info_file_path=f'info/info-{self.info["id"]}.json',
            url=self.content_url,
        )
        with CustomYoutubeDL(self.main_downloader_obj.options) as ytdl_obj:
            with open(similar_content.info_file_path, 'w') as info_file:
                json.dump(ytdl_obj.sanitize_info(self.info), info_file)
            info = self.main_downloader_obj.extract_info(ytdl_obj)
            self.assertIsInstance(info, dict)
            self.assertEqual(info.get('original_url', None), self.content_url)
            self.assertEqual(self.info['id'], info['id'])
            self.assertEqual(self.info['id'], self.main_downloader_obj.info['id'])
            self.assertEqual(self.main_downloader_obj.info_file_path, f'info/info-{self.info['id']}.json')

    def test_custom_downloader_selection(self):
        """
            Tests custom downloader selection of MainDownloader for a specific url and extractor.
            It should find the correct custom downloader class and return an initialized instance of it.
        """
        with CustomYoutubeDL(self.main_downloader_obj.options) as ytdl_obj:
            custom_downloader = self.main_downloader_obj.get_custom_downloader(ytdl_obj)
            self.assertIsInstance(custom_downloader, BaseDownloader)
            self.assertIsInstance(custom_downloader, YoutubeDownloader)
            self.assertEqual(custom_downloader.url, self.content_url)

    def test_content_downloading(self):
        """
            Tests downloading a content using url functionality of MainDownloader.
            It should download the content using custom_downloader or default functionality.
            It should set downloaded_successfully true.
        """
        with CustomYoutubeDL(self.main_downloader_obj.options) as ytdl_obj:
            self.assertFalse(self.main_downloader_obj.downloaded_successfully)
            code, ytdl_obj = self.main_downloader_obj.download(ytdl_obj, fake=False)
            content_path = self.main_downloader_obj.get_download_path(ytdl_obj)
            self.assertTrue(os.path.exists(content_path))
            self.assertTrue(os.path.isfile(content_path))
            self.assertTrue(self.main_downloader_obj.downloaded_successfully)

    def test_content_fake_downloading(self):
        """
            Tests fake downloading a content using url functionality of MainDownloader.
            It should not download the content.
            It should set downloaded_successfully true.
        """
        with CustomYoutubeDL(self.main_downloader_obj.options) as ytdl_obj:
            self.assertFalse(self.main_downloader_obj.downloaded_successfully)
            content_path = self.main_downloader_obj.get_download_path(ytdl_obj)
            if os.path.exists(content_path):
                wait_until_file_is_being_processed_then_delete(content_path, tries=5)
            self.main_downloader_obj.download(ytdl_obj, fake=True)
            self.assertFalse(os.path.exists(content_path))
            self.assertTrue(self.main_downloader_obj.downloaded_successfully)

    def test_content_obj_creation(self):
        """
            Tests Content object creation for the download process of MainDownloader.
            It should set content_obj.
        """
        with CustomYoutubeDL(self.main_downloader_obj.options) as ytdl_obj:
            self.assertEqual(Content.objects.count(), 0)
            content_obj = self.main_downloader_obj.get_content_obj(ytdl_obj)
            self.assertEqual(Content.objects.count(), 1)
            self.assertEqual(content_obj, Content.objects.first())
            self.assertEqual(content_obj.url, self.content_url)

    def test_pre_created_content_obj_updating(self):
        """
            Tests pre-created content object updating of MainDownloader.
            It should use pre_created_content_obj to set content_obj.
        """
        pre_created_content_obj = Content.objects.create(
            url=self.content_url,
            info_id=self.info['id'],
            info_file_path=self.info['info_file_path'],
        )
        self.assertEqual(Content.objects.count(), 1)
        self.main_downloader_obj.pre_created_content_obj = pre_created_content_obj
        with CustomYoutubeDL(self.main_downloader_obj.options) as ytdl_obj:
            self.assertIsNone(pre_created_content_obj.title)
            content_obj = self.main_downloader_obj.get_content_obj(ytdl_obj)
            self.assertEqual(content_obj.pk, pre_created_content_obj.pk)
            self.assertEqual(content_obj, self.main_downloader_obj.content_obj)
            self.assertEqual(content_obj.url, pre_created_content_obj.url)
            self.assertEqual(content_obj.title, self.info['title'])
            self.assertEqual(Content.objects.count(), 1)

    def test_run_method(self):
        """
            Tests run method of the MainDownloader which is the only method should be run when no overriding needed.
            It should set up ytdl_obj properly.
            It should get info of the url properly.
            It should download the content properly.
            It should set content object properly.
        """

        # download=True
        code, info, content_obj, ytdl_obj = self.main_downloader_obj.run(download=True)
        self.assertEqual(code, 0)
        self.assertEqual(info['original_url'], self.content_url)
        self.assertEqual(info['id'], self.info['id'])
        self.assertIsInstance(content_obj, Content)
        self.assertEqual(content_obj.url, self.content_url)
        self.assertEqual(content_obj.info_id, info['id'])
        self.assertEqual(content_obj.info_file_path, info['info_file_path'])
        self.assertTrue(os.path.exists(self.main_downloader_obj.get_download_path(ytdl_obj)))
        self.assertTrue(os.path.isfile(content_obj.download_path))
        self.assertIsInstance(ytdl_obj, CustomYoutubeDL)
        wait_until_file_is_being_processed_then_delete(content_obj.download_path, tries=5)

        # download=False
        code, info, content_obj, ytdl_obj = self.main_downloader_obj.run(download=False)
        self.assertEqual(code, 0)
        self.assertEqual(info['original_url'], self.content_url)
        self.assertEqual(info['id'], self.info['id'])
        self.assertIsInstance(content_obj, Content)
        self.assertEqual(content_obj.url, self.content_url)
        self.assertEqual(content_obj.info_id, info['id'])
        self.assertEqual(content_obj.info_file_path, info['info_file_path'])
        self.assertFalse(os.path.exists(content_obj.download_path))
        self.assertIsInstance(ytdl_obj, CustomYoutubeDL)

    def test_download_process_error_raise(self):
        """
            Tests error handling functionality of the MainDownloader.
            It should raise DownloadProcessError for any error during the process.
        """
        self.main_downloader_obj.url = 'wrong url'
        self.assertRaises(DownloadProcessError, self.main_downloader_obj.run, download=True)
        # try:
        #     self.main_downloader_obj.run(download=True)
        # except Exception as error:
        #     self.assertIsInstance(error, DownloadProcessError)
        # else:
        #     self.fail('Did not raised DownloadProcessError for a wrong url!')


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
)
class MainDownloaderAsyncTasksTests(TestCase):

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
            detail={'type': 'video', 'resolution': 360, 'extension': 'mp4'}
        )
        with CustomYoutubeDL(cls.main_downloader_obj.options) as ytdl_obj:
            cls.info = cls.main_downloader_obj.extract_info(ytdl_obj)
            cls.download_path = cls.main_downloader_obj.get_download_path(ytdl_obj)

    def test_async_extract_info(self):
        result = async_extract_info.delay(self.content_url, self.main_downloader_obj.detail)
        info = result.get()
        self.assertTrue(result.successful())
        self.assertEqual(info['id'], self.info['id'])
        self.assertEqual(Content.objects.count(), 0)
        self.assertFalse(os.path.exists(self.download_path))

    def test_async_process_url(self):
        result = async_process_url.delay(self.content_url, self.main_downloader_obj.detail)
        code, info, content_pk = result.get()
        self.assertTrue(result.successful())
        self.assertEqual(code, 0)
        self.assertEqual(info['id'], self.info['id'])
        self.assertEqual(Content.objects.count(), 1)
        self.assertEqual(Content.objects.first().pk, content_pk)
        self.assertEqual(Content.objects.first().url, self.content_url)
        self.assertFalse(os.path.exists(self.download_path))

    def test_async_download_content(self):
        result = async_download_content.delay(self.content_url, self.main_downloader_obj.detail)
        code, info, content_pk = result.get()
        self.assertTrue(result.successful())
        self.assertEqual(code, 0)
        self.assertEqual(info['id'], self.info['id'])
        self.assertEqual(Content.objects.count(), 1)
        content_obj = Content.objects.first()
        self.assertEqual(content_obj.pk, content_pk)
        self.assertEqual(content_obj.url, self.content_url)
        self.assertTrue(os.path.exists(content_obj.download_path))
        self.assertTrue(os.path.isfile(content_obj.download_path))
        wait_until_file_is_being_processed_then_delete(content_obj.download_path, tries=5)


    def test_async_tasks_combination(self):
        # processing url (info extraction, pre_created_content_obj creation, not downloading)
        process_url_result = async_process_url.delay(self.content_url, self.main_downloader_obj.detail)
        code, info, pre_created_content_pk = process_url_result.get()
        self.assertTrue(process_url_result.successful())
        # downloading content using the data obtained during url processing
        download_content_result = async_download_content.delay(
            self.content_url, self.main_downloader_obj.detail, info=info,
            info_file_path=info.get('info_file_path', None), pre_created_content_obj=pre_created_content_pk
        )
        code, info, content_pk = download_content_result.get()
        self.assertTrue(download_content_result.successful())
        self.assertEqual(code, 0)
        self.assertEqual(content_pk, pre_created_content_pk)
        self.assertEqual(Content.objects.count(), 1)
        content_obj = Content.objects.first()
        self.assertEqual(content_obj.pk, content_pk)
        self.assertTrue(os.path.exists(content_obj.download_path))
        self.assertTrue(os.path.isfile(content_obj.download_path))
        wait_until_file_is_being_processed_then_delete(content_obj.download_path, tries=5)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_STORE_EAGER_RESULT=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
)
class DownloadContentViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.youtube_extractor = AllowedExtractor.objects.create(
            name='youtube',
            regex='^youtube',
            active=True,
        )
        cls.content_url = 'https://youtu.be/2PuFyjAs7JA?si=R6UuXVl-BPr-niXv'
        cls.content = Content.objects.create(
            info_id='2PuFyjAs7JA',
            info_file_path='info/info-2PuFyjAs7JA.json',
            url=cls.content_url,
            title='test content',
            type='audio',
            extension='mp3',
            audio_bitrate=320,
        )
        cls.path = reverse('download-content', kwargs={'pk': cls.content.pk})

    def test_view_url(self):
        self.assertEqual(resolve(self.path).func.__name__, DownloadContentView.as_view().__name__)

    def test_view_separately(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.content.refresh_from_db()
        self.assertTrue(self.content.downloaded_successfully)
        self.assertIsNotNone(self.content.download_path)
        self.assertTrue(os.path.exists(self.content.download_path))
        self.assertTrue(os.path.isfile(self.content.download_path))
        self.assertIsInstance(response, FileResponse)
        self.assertIn('attachment;', response.get('Content-Disposition', None))
        self.assertEqual(response.get('Content-Type', None), 'audio/mpeg')
        wait_until_file_is_being_processed_then_delete(self.content.download_path, 5)

    def test_view_with_download_started_content_get(self):
        detail = {'type': 'audio', 'audio_bitrate': 320, 'extension': 'mp3'}
        download_result = async_download_content.delay(self.content_url, detail=detail)
        _, info, content_pk = download_result.get()
        content = Content.objects.get(pk=content_pk)
        content.celery_download_task_id = download_result.task_id
        content.save()
        path = reverse('download-content', kwargs={'pk': content.pk})
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content.refresh_from_db()
        self.assertTrue(content.downloaded_successfully)
        self.assertIsNotNone(content.download_path)
        self.assertTrue(os.path.exists(content.download_path))
        self.assertTrue(os.path.isfile(content.download_path))
        self.assertIsInstance(response, FileResponse)
        self.assertIn('attachment;', response.get('Content-Disposition', None))
        self.assertEqual(response.get('Content-Type', None), 'audio/mpeg')
        wait_until_file_is_being_processed_then_delete(content.download_path, 5)


def wait_until_file_is_being_processed_then_delete(file_path, tries=5):
    for i in range(tries):
        try:
            print('trying to delete the file')
            os.remove(file_path)
        except PermissionError as e:
            time.sleep(3)
        else:
            break