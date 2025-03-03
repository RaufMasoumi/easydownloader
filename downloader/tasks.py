from config.settings import BASE_DIR
from . import downloaders
from .models import Content, AllowedExtractor
from celery import shared_task
import os
from yt_dlp.utils import (YoutubeDLError, ExtractorError, UnsupportedError, UserNotLive,
                          DownloadError, PostProcessingError, DownloadCancelled)
import json
import inspect
import re
import os

downloaders_list = [(name, obj, getattr(obj, 'extractor', ''))
                    for name, obj in inspect.getmembers(downloaders, inspect.isclass)
                    if getattr(obj, 'is_downloader', False)]
downloaders_dict = {extractor: downloader_obj for _, downloader_obj, extractor in downloaders_list}
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
        if info.get('extractor').lower() in downloaders_dict.keys():
            downloader_class_obj = downloaders_dict[info.get('extractor').lower()]
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


def delete_expired_content_files():
    expired_but_not_processed_contents = Content.objects.expired_contents().filter(expired=False)
    objs = []
    for content in expired_but_not_processed_contents:
        file_path = content.download_path
        if file_path and os.path.exists(file_path):
            print(f'content file {file_path} expired, removing it...')
            os.remove(file_path)
        content.download_path = None
        content.expired = True
        objs.append(content)
    Content.objects.bulk_update(objs, ['download_path', 'expired'])
