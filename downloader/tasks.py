from config.settings import BASE_DIR
from . import downloaders
from celery import shared_task
import os
import yt_dlp
import json
import inspect

downloader_functions = [func for func, obj in inspect.getmembers(downloaders, inspect.isfunction)]


@shared_task
def test_task(word: str):
    return f'hello {word}'


# def generate_format_selection_string(format_data: dict):
#     format_string = ''
#
#     if format_data.get('type') == 'video':
#         format_string += 'bestvideo{}+bestaudio{}/best{}'
#     else:
#         format_string += 'bestaudio{}'
#
#     if format_data.get('resolution'):
#         resolution = format_data['resolution']
#         resolution = resolution[:-1] if resolution.endswith('p') else resolution
#
#     if format_data.get('extension'):

#
#
# def download_content(url, where_to_save='temp'):
#     options = {
#         'format': 'best',  # Download the best available audio
#         'outtmpl': str(BASE_DIR / os.path.join(where_to_save, '%(title)s.%(ext)s')),  # Set the output file template
#         'verbos': True
#     }
#
#     with yt_dlp.YoutubeDL(options) as downloader:
#         info = downloader.extract_info(url, download=False)
#         print('starting download:')
#         download_code = downloader.download_with_info_file()
#         # downloader.download(url) no need to download it again!
#         return info, download_code


def download_content(url, where_to_save='temp'):
    options = {
        'format': 'best',  # Download the best available audio
        'outtmpl': str(BASE_DIR / os.path.join(where_to_save, '%(title)s.%(ext)s')),  # Set the output file template
        'verbos': True
    }
    with yt_dlp.YoutubeDL(options) as main_downloader:
        info = main_downloader.extract_info(url, download=False)
        info_file_path = 'info/info-{info_id}.json'.format(info_id=info['id'])
        with open(info_file_path, 'w') as info_file:
            json.dump(main_downloader.sanitize_info(info), info_file)
        print('checking the customized function:')
        if info.get('extractor') in downloader_functions:
            downloader_function = getattr(downloaders, info['extractor'])
            return downloader_function(url, where_to_save, info, info_file_path, main_downloader, options)
        else:
            print('there is no customized function, downloading with the defaults:')
            code = main_downloader.download_with_info_file(info_file_path)
            print('downloaded successfully!')
            return info, code
