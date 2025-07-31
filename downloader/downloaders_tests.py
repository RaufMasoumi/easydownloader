from django.test import TestCase
import os
from .models import AllowedExtractor
from .downloaders import YoutubeDownloader, InstagramDownloader, CustomYoutubeDL
from .main_downloader import MainDownloader

class YoutubeDownloaderTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.youtube_extractor = AllowedExtractor.objects.create(
            name='youtube',
            regex='^youtube',
            active=True,
        )
        cls.content_url = 'https://youtu.be/2PuFyjAs7JA?si=R6UuXVl-BPr-niXv'
        cls.video_detail = {
            # correct data
            'type': 'video',
            'resolution': 360,
            'extension': 'mp4',
            'frame_rate': 60,
            # wrong data
            'audio_bitrate': 400,
        }
        cls.audio_detail = {
            # correct data
            'type': 'audio',
            'audio_bitrate': 400,
            'extension': 'mp3',
            # wrong data
            'resolution': 360,

        }
        cls.video_main_downloader_obj = MainDownloader(
            url=cls.content_url,
            detail=cls.video_detail,
        )
        cls.audio_main_downloader_obj = MainDownloader(
            url=cls.content_url,
            detail=cls.audio_detail,
        )
        with CustomYoutubeDL(cls.video_main_downloader_obj.options) as ytdl_obj:
            cls.info = cls.video_main_downloader_obj.extract_info(ytdl_obj)
            cls.info_file_path = cls.info.get('info_file_path', None)

    def setUp(self):
        self.video_youtube_downloader_obj = YoutubeDownloader(
            self.content_url, detail=self.video_detail, info=self.info, info_file_path=self.info_file_path,
            default_options=self.video_main_downloader_obj.options, main_downloader_obj=self.video_main_downloader_obj,
        )
        self.audio_youtube_downloader_obj = YoutubeDownloader(
            self.content_url, detail=self.audio_detail, info=self.info, info_file_path=self.info_file_path,
            default_options=self.audio_main_downloader_obj.options, main_downloader_obj=self.audio_main_downloader_obj,
        )

    def test_video_format_selection(self):
        self.assertEqual(
            self.video_youtube_downloader_obj.get_options().get('format', None),
            'bestvideo[ext=mp4]+bestaudio/bestvideo+bestaudio/best/best*'
        )
        self.assertEqual(
            self.video_youtube_downloader_obj.get_options().get('merge_output_format', None),
            f'{self.video_detail['extension']}/mp4/mkv/webm'
        )

    def test_audio_format_selection(self):
        self.assertEqual(
            self.audio_youtube_downloader_obj.get_options().get('format', None),
            'bestaudio[ext=mp3]/bestaudio/best'
        )

    def test_video_format_sort_list(self):
        self.assertListEqual(
            self.video_youtube_downloader_obj.get_options().get('format_sort', None),
            [f'height~{self.video_detail['resolution']}', f'fps~{self.video_detail['frame_rate']}']
        )

    def test_audio_format_sort_list(self):
        self.assertListEqual(
            self.audio_youtube_downloader_obj.get_options().get('format_sort', None),
            [f'abr~{self.audio_detail['audio_bitrate']}', ]
        )

    def test_video_postprocessors_list(self):
        self.assertListEqual(
            self.video_youtube_downloader_obj.get_options().get('postprocessors', None),
            [
                {
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': f'{self.video_detail['extension']}',
                },
                {
                    'key': 'EmbedThumbnail',
                    'already_have_thumbnail': False,
                },
                {
                    'key': 'FFmpegMetadata',
                },
            ]
        )

    def test_audio_postprocessors_list(self):
        self.assertListEqual(
            self.audio_youtube_downloader_obj.get_options().get('postprocessors', None),
            [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': f'{self.audio_detail['extension']}',
                    'preferredquality': f'{self.audio_detail['audio_bitrate']}',
                },
                {
                    'key': 'EmbedThumbnail',
                    'already_have_thumbnail': False,
                },
                {
                    'key': 'FFmpegMetadata',
                },
            ]
        )


    def test_video_content_downloading(self):
        code, _, ytdl_obj = self.video_youtube_downloader_obj.download(fake=False)
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(self.video_main_downloader_obj.get_download_path(ytdl_obj)))
        self.assertTrue(os.path.isfile(self.video_main_downloader_obj.get_download_path(ytdl_obj)))
        os.remove(self.video_main_downloader_obj.get_download_path(ytdl_obj))
        # fake downloading
        code, _, _ = self.video_youtube_downloader_obj.download(fake=True)
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.video_main_downloader_obj.get_download_path(ytdl_obj)))

    def test_audio_content_downloading(self):
        code, _, ytdl_obj = self.audio_youtube_downloader_obj.download(fake=False)
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(self.audio_main_downloader_obj.get_download_path(ytdl_obj)))
        self.assertTrue(os.path.isfile(self.audio_main_downloader_obj.get_download_path(ytdl_obj)))
        os.remove(self.audio_main_downloader_obj.get_download_path(ytdl_obj))
        # fake downloading
        code, _, _ = self.audio_youtube_downloader_obj.download(fake=True)
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.audio_main_downloader_obj.get_download_path(ytdl_obj)))

    def test_main_downloader_uses_youtube_downloader(self):
        with CustomYoutubeDL(self.video_main_downloader_obj.options) as ytdl_obj:
            self.assertIsInstance(self.video_main_downloader_obj.get_custom_downloader(ytdl_obj), YoutubeDownloader)


class InstagramDownloaderTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.instagram_extractor = AllowedExtractor.objects.create(
            name='instagram',
            regex='^instagram',
            active=True,
        )
        cls.content_url = 'https://www.instagram.com/reel/DGc3h9VT5Lt/?igsh=MTJ3dTFsMXB5ZDNoZA=='
        cls.video_detail = {
            # correct data
            'type': 'video',
            'resolution': 360,
            'extension': 'mp4',
            'frame_rate': 60,
            # wrong data
            'audio_bitrate': 400,
        }
        cls.audio_detail = {
            # correct data
            'type': 'audio',
            'audio_bitrate': 400,
            'extension': 'mp3',
            # wrong data
            'resolution': 360,

        }
        cls.main_downloader_obj = MainDownloader(
            url=cls.content_url,
            detail=cls.video_detail,
        )
        with CustomYoutubeDL(cls.main_downloader_obj.options) as cls.ytdl_obj:
            cls.info = cls.main_downloader_obj.extract_info(cls.ytdl_obj)
            cls.info_file_path = cls.info.get('info_file_path', None)


    def test_main_downloader_uses_instagram_downloader(self):
        with CustomYoutubeDL(self.main_downloader_obj.options) as ytdl_obj:
            self.assertIsInstance(self.main_downloader_obj.get_custom_downloader(ytdl_obj), InstagramDownloader)