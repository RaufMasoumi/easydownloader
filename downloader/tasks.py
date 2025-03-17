from errno import errorcode

from celery import shared_task
from .models import Content
from .main_downloader import MainDownloader
from .downloaders import CustomYoutubeDL
import os


@shared_task
def test_task(word: str):
    return f'hello {word}'

@shared_task
def async_extract_info(*args, **kwargs):
    downloader = MainDownloader(*args, **kwargs)
    with CustomYoutubeDL(downloader.options) as main_ytdl_obj:
        info = downloader.extract_info(main_ytdl_obj)
    return info

@shared_task
def async_download_content(*args, **kwargs):
    downloader = MainDownloader(*args, **kwargs)
    error_code, info, content, ytdl_obj = downloader.run()
    return error_code

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
