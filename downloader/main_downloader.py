import inspect
import json
import os
import re
from yt_dlp.utils import (DownloadError, DownloadCancelled,
                          UnsupportedError, UserNotLive, ExtractorError, PostProcessingError, YoutubeDLError)
from config.settings import BASE_DIR
from . import downloaders
from .downloaders import CustomYoutubeDL
from .models import Content, AllowedExtractor

allowed_extractors_regexes_list = [extractor.regex for extractor in AllowedExtractor.objects.active_extractors()]
DOWNLOADERS_LIST = [(name, obj, getattr(obj, 'extractor', ''))
                    for name, obj in inspect.getmembers(downloaders, inspect.isclass)
                    if getattr(obj, 'is_downloader', False)]
DOWNLOADERS_DICT = {extractor: downloader_obj for _, downloader_obj, extractor in DOWNLOADERS_LIST}

class DownloadProcessError(Exception):

    def __init__(self, msg=None):
        self.msg = msg if msg else "An error occurred while downloading the content!"
        self.msg += "  Please try again or enter another link."
        super().__init__(self.msg)

def raise_download_process_error(func):
    def wrapper(*args, **kwargs):
        try:
            return_values = func(*args, **kwargs)

        except UnsupportedError as error:
            raise DownloadProcessError("Unsupported URL!") from error
        except UserNotLive as error:
            raise DownloadProcessError("The channel is not currently live!") from error
        except ExtractorError as error:
            raise DownloadProcessError("Could not extract the info of given url content!") from error
        except DownloadError as error:
            raise DownloadProcessError("Could not download the content!") from error
        except DownloadCancelled as error:
            raise DownloadProcessError("The download process cancelled!") from error
        except PostProcessingError as error:
            raise DownloadProcessError("An error occurred while post processing the content!") from error
        except YoutubeDLError as error:
            raise DownloadProcessError() from error

        else:
            return  return_values

    return wrapper


@raise_download_process_error
def download_content(url, where_to_save='temp', format_data=None):
    options = {
        'format': 'bestvideo+bestaudio/best/best*',
        'outtmpl': str(BASE_DIR / os.path.join(where_to_save, '%(title)s.%(ext)s')),
        'allowed_extractors': allowed_extractors_regexes_list,
        'verbos': True,
        'writethumbnail': True,
        'postprocessors': [
            {
                'key': 'FFmpegMetadata',
            },
            {
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False,
            }
        ]
    }
    with downloaders.CustomYoutubeDL(options) as downloader:
        print('starting download process...')
        error_code = 1
        related_downloaded_contents = Content.objects.filter(url=url)
        if related_downloaded_contents.exists():
            info_file_path = related_downloaded_contents.order_by('-processed_at').first().info_file_path
            with open(info_file_path) as info_file:
                info = json.load(info_file)
        else:
            info = downloader.extract_info(url, download=False)
            info_file_path = f'info/info-{info['id']}.json'
            with open(info_file_path, 'w') as info_file:
                json.dump(downloader.sanitize_info(info), info_file)
        print('checking the customized function:')
        if info.get('extractor').lower() in DOWNLOADERS_DICT.keys():
            downloader_class_obj = DOWNLOADERS_DICT[info.get('extractor').lower()]
            info, error_code, downloader = downloader_class_obj(url, where_to_save=where_to_save,
                                               info=info, info_file_path=info_file_path,
                                               default_options=options, main_downloader_obj=downloader, format_data=format_data).download()
        # for class_name, obj in downloaders_list:
        #     if info.get('extractor').lower() == class_name.lower().replace('downloader', ''):
        #         info, error_code, downloader = obj(url, where_to_save=where_to_save,
        #                    info=info, info_file_path=info_file_path,
        #                    default_options=options, main_downloader_obj=downloader, format_data=format_data).download()
        else:
            if error_code:
                print('there is no customized function, downloading with the defaults:')
                error_code = downloader.download_with_info_file(info_file_path)
        download_path = downloader.prepare_filename(info)
        download_path = re.sub(r'\.[^.\\]+$', f'.{format_data['extension']}', download_path) if format_data.get('extension') else download_path
        Content.objects.create(
            info_id=info['id'],
            info_file_path=info_file_path,
            url=info.get('original_url') or info.get('webpage_url'),
            title=info.get('title'),
            download_path=download_path,
            successful=False if error_code else True,
        )
        print('downloaded successfully!')
        return info, error_code, downloader


class MainDownloader:
    download_dir = 'temp'
    default_options = {
        'format': 'bestvideo+bestaudio/best/best*',
        'outtmpl': str(BASE_DIR / os.path.join(download_dir, '%(title)s.%(ext)s')),
        'allowed_extractors': allowed_extractors_regexes_list,
        'verbos': True,
        'writethumbnail': True,
        'postprocessors': [
            {
                'key': 'FFmpegMetadata',
            },
            {
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False,
            }
        ]
    }
    def __init__(self, url, detail=None, options=None):
        self.url = url
        self.detail = detail or {}
        self.has_custom_downloader = False
        self.custom_downloader = None
        self.downloaded_successfully = False
        self.content_obj = None
        self.info = None
        self.info_file_path = None
        self.content = None
        options = options or dict()
        options.update(
            self.default_options
        )
        self.options = options


    def get_custom_downloader(self, main_ytdl_obj):
        info = self.extract_info()
        if not self.has_custom_downloader:
            if info.get('extractor').lower() in DOWNLOADERS_DICT.keys():
                self.custom_downloader = DOWNLOADERS_DICT[info.get('extractor').lower()]
                self.has_custom_downloader = True
        if self.has_custom_downloader:
            initialized_custom_downloader = self.custom_downloader(self.url, where_to_save=self.download_dir,
                                                   info=self.info, info_file_path=self.info_file_path,
                                                   default_options=self.options, main_downloader_obj=main_ytdl_obj, format_data=self.detail)
            return initialized_custom_downloader
        else:
            return None

    def extract_info(self, ytdl_obj=None):
        if getattr(self, 'info', None):
            return self.info

        related_downloaded_contents = Content.objects.filter(url=self.url)
        if related_downloaded_contents.exists():
            self.info_file_path = related_downloaded_contents.order_by('-processed_at').first().info_file_path
            with open(self.info_file_path) as info_file:
                self.info = json.load(info_file)
        else:
            self.info = ytdl_obj.extract_info(self.url, download=False)
            self.info_file_path = f'info/info-{self.info['id']}.json'
            with open(self.info_file_path, 'w') as info_file:
                json.dump(ytdl_obj.sanitize_info(self.info), info_file)

        return self.info


    def download(self, ytdl_obj):
        error_code = 1
        if self.downloaded_successfully:
            return 0
        custom_downloader = self.get_custom_downloader(ytdl_obj)
        if custom_downloader:
            custom_downloader = self.get_custom_downloader(ytdl_obj)
            error_code, info, ytdl_obj = custom_downloader.download()
        else:
            error_code = ytdl_obj.download_with_info_file(self.info_file_path)
        self.downloaded_successfully = not error_code
        return error_code, ytdl_obj


    def get_content_obj(self, ytdl_obj):
        if getattr(self, 'content_obj', None):
            return self.content_obj

        info = self.extract_info()
        download_path = ytdl_obj.prepare_filename(info)
        download_path = re.sub(
            r'\.[^.\\]+$', f'.{self.detail['extension']}', download_path
        ) if self.detail.get('extension') else download_path
        self.content_obj = Content.objects.create(
            info_id=info['id'],
            info_file_path=self.info_file_path,
            url=info.get('original_url') or info.get('webpage_url'),
            title=info.get('title'),
            download_path=download_path,
            successful=self.downloaded_successfully,
        )
        return self.content_obj

    @raise_download_process_error
    def run(self, download=True):
        with CustomYoutubeDL(self.options) as main_ytdl_obj:
            info = self.extract_info(main_ytdl_obj)
            error_code, ytdl_obj = self.download(main_ytdl_obj) if download else (0, main_ytdl_obj)
            content = self.get_content_obj(ytdl_obj)
        return error_code, info, content, ytdl_obj


