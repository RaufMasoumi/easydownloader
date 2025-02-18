from config.settings import BASE_DIR
from . import downloaders
from .models import AllowedExtractor
from celery import shared_task
import os
import yt_dlp
from yt_dlp.utils import (YoutubeDLError, ExtractorError, UnsupportedError, UserNotLive,
                          DownloadError, PostProcessingError, DownloadCancelled)
import json
import inspect

downloaders_list = inspect.getmembers(downloaders, inspect.isclass)
allowed_extractors_regexes_list = [extractor.regex for extractor in AllowedExtractor.objects.active_extractors()]

@shared_task
def test_task(word: str):
    return f'hello {word}'


class DownloadProcessError(Exception):

    def __init__(self, msg=None):
        self.msg = msg if msg else "An error occurred while downloading the content!"
        self.msg += "  Please try again or enter another link."
        super().__init__(self.msg)


def raise_download_process_error(func):
    def wrapper(*args, **kwargs):
        try:
            info, code = func(*args, **kwargs)

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
            return info, code

    return wrapper


@raise_download_process_error
def download_content(url, where_to_save='temp', format_data=None):
    options = {
        'format': 'best*',
        'outtmpl': str(BASE_DIR / os.path.join(where_to_save, '%(title)s.%(ext)s')),
        'allowed_extractors': allowed_extractors_regexes_list,
        'verbos': True,
    }
    with yt_dlp.YoutubeDL(options) as main_downloader:
        print('starting download process...')
        info = main_downloader.extract_info(url, download=False)
        info_file_path = f'info/info-{info['id']}.json'
        with open(info_file_path, 'w') as info_file:
            json.dump(main_downloader.sanitize_info(info), info_file)
        print('checking the customized function:')
        for class_name, obj in downloaders_list:
            if info.get('extractor') == class_name.lower().replace('downloader', ''):
                return obj(url, where_to_save=where_to_save,
                           info=info, info_file_path=info_file_path,
                           default_options=options, main_downloader_obj=main_downloader, format_data=format_data).download()
        print('there is no customized function, downloading with the defaults:')
        code = main_downloader.download_with_info_file(info_file_path)
        print('downloaded successfully!')
        return info, code