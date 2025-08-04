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
def async_process_url(*args, **kwargs):
    kwargs = update_kwargs_content_obj(kwargs, ['content_obj', 'pre_created_content_obj'])
    downloader = MainDownloader(*args, **kwargs)
    code, info, content, ytdl_obj = downloader.run(download=False)
    return code, info, content.pk


@shared_task
def async_download_content(*args, **kwargs):
    kwargs = update_kwargs_content_obj(kwargs, ['content_obj', 'pre_created_content_obj'])
    downloader = MainDownloader(*args, **kwargs)
    code, info, content, ytdl_obj = downloader.run(download=True)
    return code, info, content.pk


@shared_task
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
    return 0


def update_kwargs_content_obj(kwargs, update_fields):
    for field in update_fields:
        if kwargs.get(field):
            try:
                obj = Content.objects.get(pk=kwargs[field])
            except Content.DoesNotExist:
                pass
            else:
                kwargs[field] = obj
    return kwargs
