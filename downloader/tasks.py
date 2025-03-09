from .models import Content
from celery import shared_task
import os


@shared_task
def test_task(word: str):
    return f'hello {word}'


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
