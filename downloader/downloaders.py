from config.settings import BASE_DIR
import os
import yt_dlp
from PIL import Image


class ThumbnailEditedYoutubeDL(yt_dlp.YoutubeDL):
    # making the thumbnails 1:1
    def _write_thumbnails(self, label, info_dict, filename, thumb_filename_base=None):
        ret = super()._write_thumbnails(label, info_dict, filename, thumb_filename_base)
        if ret:
            print('changing the cover...')
            for _, thumbnail_file_name in ret:
                try:
                    with Image.open(thumbnail_file_name) as img:
                        width, height = img.size
                        min_dimension = min(height, width)
                        left = (width - min_dimension) // 2
                        top = (height - min_dimension) // 2
                        right = (width + min_dimension) // 2
                        bottom = (height + min_dimension) // 2
                        box = (left, top, right, bottom)
                        img.crop(box).save(thumbnail_file_name)
                except:
                    pass
        return ret

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
        postprocessors = self.options.get('postprocessors', [])
        if self.is_video:
            filter_string = ''
            if self.format_data.get('extension'):
                filter_string += '[ext={extension}]'.format(extension=self.format_data['extension'])
                self.options.update(
                    {
                        'merge_output_format': '/'.join([self.format_data['extension'], 'mp4', 'mkv', 'webm']),
                    }
                )
                postprocessors += [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': f'{self.format_data['extension']}',
                    }, ]
            if self.format_data.get('aspect_ratio'):
                filter_string += '[aspect_ratio={aspect_ratio}]'.format(aspect_ratio=self.format_data['aspect_ratio'])
            translated_format += f'bestvideo{filter_string}+bestaudio/bestvideo+bestaudio/best'

        else:
            filter_string = ''
            if self.format_data.get('extension'):
                filter_string += '[ext={extension}]'.format(extension=self.format_data['extension'])
                audio_converter_postprocessor = {
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': f'{self.format_data["extension"]}',
                }
                if self.format_data.get('bitrate'):
                    audio_converter_postprocessor.update({
                        'preferredquality': f'{self.format_data["bitrate"]}',
                    })
                postprocessors += [audio_converter_postprocessor, ]
            translated_format += f'bestaudio{filter_string}/bestaudio/best'
        self.options['postprocessors'] = postprocessors
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
        self.options.get('postprocessors', []).reverse()
        return self.options

    def download(self):
        print('this is the customized download function for youtube!')
        code = 1
        print(self.get_options())
        youtubedl = yt_dlp.YoutubeDL if self.is_video else ThumbnailEditedYoutubeDL
        with youtubedl(self.get_options()) as downloader:
            print('downloading:')
            if self.info_file_path:
                code = downloader.download_with_info_file(self.info_file_path)
            else:
                self.info = downloader.extract_info(self.url, download=True)
                if self.info:
                    code = 0
            print('file downloaded successfully')
            return self.info, code


class InstagramDownloader(YoutubeDownloader):
    def get_options(self):
        options = super().get_options()
        options.update({
            'outtmpl': str(BASE_DIR / os.path.join(self.where_to_save, 'instagram-%(title)s.%(ext)s')),
        })
        return options