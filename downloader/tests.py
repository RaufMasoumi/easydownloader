from django.test import TestCase, override_settings
import json
import os.path
from .main_downloader import MainDownloader, CustomYoutubeDL, DownloadProcessError
from .downloaders import BaseDownloader, YoutubeDownloader
from .models import Content, AllowedExtractor
from .tasks import async_extract_info, async_process_url, async_download_content
# Create your tests here.


class MainDownloaderTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.youtube_extractor = AllowedExtractor.objects.create(
            name='youtube',
            regex='^youtube',
            active=True,
        )
        cls.content_url = 'https://youtu.be/2PuFyjAs7JA?si=R6UuXVl-BPr-niXv'
        with CustomYoutubeDL() as ytdl_obj:
            cls.info = ytdl_obj.extract_info(cls.content_url, download=False)
            cls.info['info_file_path'] = f'info/info-{cls.info['id']}.json'

    def setUp(self):
        self.main_downloader_obj = MainDownloader(
            url=self.content_url,
            detail={'type': 'video', 'resolution': 360, 'extension': 'mp4'},
        )


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
                os.remove(content_path)
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
        os.remove(content_obj.download_path)

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
        try:
            self.main_downloader_obj.run(download=True)
        except Exception as error:
            self.assertIsInstance(error, DownloadProcessError)
        else:
            self.fail('Did not raised DownloadProcessError for a wrong url!')


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
        os.remove(content_obj.download_path)


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
        os.remove(content_obj.download_path)
