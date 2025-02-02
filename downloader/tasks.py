from config.settings import BASE_DIR
from celery import shared_task
import os
import yt_dlp

@shared_task
def test_task(word: str):
    return f'hello {word}'


def download_content(url, where_to_save='temp'):
    options = {
        'format': 'best',  # Download the best available audio
        'outtmpl': str(BASE_DIR / os.path.join(where_to_save, '%(title)s.%(ext)s')),  # Set the output file template
        'verbos': True
    }

    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=True)
        # downloader.download(url) no need to download it again!
        return info

