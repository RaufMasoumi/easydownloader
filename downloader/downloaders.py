from config.settings import BASE_DIR
import os
import yt_dlp


def youtube(url, where_to_save, info, info_file_path, main_downloader_obj=None, default_options=None):
    print('this is the customized download function for youtube!')
    options = default_options or {}
    options.update({
        'outtmpl': str(BASE_DIR / os.path.join(where_to_save, 'youtube-%(title)s.%(ext)s'))
    })
    with yt_dlp.YoutubeDL(options) as downloader:
        print('downloading:')
        code = downloader.download_with_info_file(info_file_path)
        print('file downloaded successfully')
        return info, code
