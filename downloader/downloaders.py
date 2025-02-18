from config.settings import BASE_DIR
import os
import yt_dlp


class YoutubeDownloader:

    def __init__(
            self, url, where_to_save='temp', info=None, info_file_path=None, default_options=None,
            main_downloader_obj=None, format_data=None
    ):
        self.url = url
        self.where_to_save = where_to_save
        self.info = info
        self.info_file_path = info_file_path
        self.options = default_options if default_options else {}
        self.main_downloader_obj = main_downloader_obj
        self.format_data = format_data if format_data else {}
        self.is_video = True if self.format_data.get('type') == 'video' else False

    def get_format(self, default_format='best'):
        if not self.format_data:
            return default_format
        translated_format = ''
        if self.is_video:
            filter_string = ''
            if self.format_data.get('extension'):
                # No need to do filtering, cause the output video will be converted
                # filter_string += '[ext={extension}]'.format(extension=self.format_data['extension'])
                self.options.update({
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': f'{self.format_data['extension']}',
                    }]
                })
            if self.format_data.get('aspect_ratio'):
                filter_string += '[aspect_ratio={aspect_ratio}]'.format(aspect_ratio=self.format_data['aspect_ratio'])
            translated_format += f'bestvideo{filter_string}+bestaudio/best'
        else:
            filter_string = ''
            if self.format_data.get('extension'):
                filter_string += '[ext={extension}]'.format(extension=self.format_data['extension'])
            translated_format += f'bestaudio{filter_string}/best'
        return translated_format

    def get_format_sort(self, default_sort=''):
        if not self.format_data:
            return default_sort if default_sort else []
        format_sort_list = []
        if self.is_video:
            if self.format_data.get('resolution'):
                format_sort_list.append('height~{resolution}'.format(resolution=self.format_data['resolution']))
            if self.format_data.get('frame_rate'):
                format_sort_list.append('fps~{frame_rate}'.format(frame_rate=self.format_data['frame_rate']))
        else:
            if self.format_data.get('bitrate'):
                format_sort_list.append('abr~{bitrate}'.format(bitrate=self.format_data['bitrate']))
        return format_sort_list

    def get_options(self):
        self.options.update({
            'outtmpl': str(BASE_DIR / os.path.join(self.where_to_save, 'youtube-%(title)s.%(ext)s')),
            'format': self.get_format(),
            'format_sort': self.get_format_sort(),
        })
        return self.options

    def download(self):
        print('this is the customized download function for youtube!')
        code = 1
        print(self.get_options())
        with yt_dlp.YoutubeDL(self.get_options()) as downloader:
            print('downloading:')
            if self.info_file_path:
                code = downloader.download_with_info_file(self.info_file_path)
            else:
                self.info = downloader.extract_info(self.url, download=True)
                if self.info:
                    code = 0
            print('file downloaded successfully')
            return self.info, code

