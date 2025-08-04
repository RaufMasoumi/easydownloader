from config.settings import BASE_DIR
import os
import yt_dlp
from yt_dlp.utils import (ExtractorError, EntryNotInPlaylist, ReExtractInfo, DownloadError, variadic)
from PIL import Image
import contextlib
import fileinput
import json
from datetime import datetime


class CustomYoutubeDL(yt_dlp.YoutubeDL):
    def __download_wrapper(self, *args, **kwargs):
        return self._YoutubeDL__download_wrapper(*args, **kwargs)

    def download_with_info_file(self, info_filename, tried_to_refresh_info=False):
        with contextlib.closing(fileinput.FileInput(
                [info_filename], mode='r',
                openhook=fileinput.hook_encoded('utf-8'))) as f:
            # FileInput doesn't have a read method, we can't call json.load
            infos = [self.sanitize_info(info, self.params.get('clean_infojson', True))
                     for info in variadic(json.loads('\n'.join(f)))]
        for info in infos:
            try:
                self.__download_wrapper(self.process_ie_result)(info, download=True)
            except (DownloadError, EntryNotInPlaylist, ReExtractInfo) as e:
                if not isinstance(e, EntryNotInPlaylist):
                    self.to_stderr('\r')
                webpage_url = info.get('webpage_url')
                if webpage_url is None:
                    raise
                # modified
                # refreshing the info file
                if not tried_to_refresh_info:
                    self.report_warning(f'It seems the info file data is expired; trying to refresh the info file')
                    new_info = self.extract_info(webpage_url, download=False)
                    with open(info_filename, 'w') as info_file:
                        json.dump(self.sanitize_info(new_info), info_file)
                    return self.download_with_info_file(info_filename, tried_to_refresh_info=True)
                else:
                    self.report_warning(f'The info failed to download: {e}; trying with URL {webpage_url}')
                    self.download([webpage_url])

            except ExtractorError as e:
                self.report_error(e)
        return self._download_retcode


class ThumbnailEditedYoutubeDL(CustomYoutubeDL):
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


class BaseDownloader:
    is_downloader = True
    extractor = ''


class YoutubeDownloader(BaseDownloader):
    extractor = 'youtube'

    def __init__(
            self, url, detail=None,  where_to_save='temp', info=None, info_file_path=None, default_options=None,
            main_downloader_obj=None,
    ):
        self.url = url
        self.where_to_save = where_to_save
        self.info = info
        self.info_file_path = info_file_path
        if self.info and not self.info_file_path and self.info.get('info_file_path', None):
            self.info_file_path = self.info['info_file_path']
        self.options = default_options if default_options else {}
        self.main_downloader_obj = main_downloader_obj
        self.detail = detail if detail else {}
        self.is_video = True if self.detail.get('type') == 'video' else False

    def get_format(self, default_format='bestvideo+bestaudio/best/best*'):
        if not self.detail:
            return default_format
        translated_format = ''
        postprocessors = self.options.get('postprocessors', [])
        if self.is_video:
            filter_string = ''
            if self.detail.get('extension'):
                filter_string += '[ext={extension}]'.format(extension=self.detail['extension'])
                self.options.update(
                    {
                        'merge_output_format': '/'.join([self.detail['extension'], 'mp4', 'mkv', 'webm']),
                    }
                )
                postprocessors += [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': f'{self.detail['extension']}',
                    }, ]
            if self.detail.get('aspect_ratio'):
                filter_string += '[aspect_ratio={aspect_ratio}]'.format(aspect_ratio=self.detail['aspect_ratio'])
            translated_format += f'bestvideo{filter_string}+bestaudio/bestvideo+bestaudio/best/best*'

        else:
            filter_string = ''
            if self.detail.get('extension'):
                filter_string += '[ext={extension}]'.format(extension=self.detail['extension'])
                self.options.update(
                    {
                        'writethumbnail': True,
                    }
                )
                audio_converter_postprocessor = {
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': f'{self.detail["extension"]}',
                }
                if self.detail.get('audio_bitrate'):
                    audio_converter_postprocessor.update({
                        'preferredquality': f'{self.detail["audio_bitrate"]}',
                    })
                postprocessors += [
                    {
                        'key': 'EmbedThumbnail',
                        'already_have_thumbnail': False,
                    },
                    audio_converter_postprocessor,
                ]
            translated_format += f'bestaudio{filter_string}/bestaudio/best'
        postprocessors = delete_copies(postprocessors)
        self.options['postprocessors'] = postprocessors
        return translated_format

    def get_format_sort(self, default_sort=''):
        if not self.detail:
            return default_sort if default_sort else []
        format_sort_list = []
        if self.is_video:
            if self.detail.get('resolution'):
                format_sort_list.append('height~{resolution}'.format(resolution=self.detail['resolution']))
            if self.detail.get('frame_rate'):
                format_sort_list.append('fps~{frame_rate}'.format(frame_rate=self.detail['frame_rate']))
        else:
            if self.detail.get('audio_bitrate'):
                format_sort_list.append('abr~{audio_bitrate}'.format(audio_bitrate=self.detail['audio_bitrate']))
        return format_sort_list

    def get_options(self):
        format_time = datetime.now().strftime('%Y%m%d%H%M%S')
        self.options.update({
            'outtmpl': str(BASE_DIR / os.path.join(self.where_to_save, f'%(title)s-{format_time}.%(ext)s')),
            'format': self.get_format(),
            'format_sort': self.get_format_sort(),
        })
        self.options.get('postprocessors', []).reverse()
        return self.options

    def download(self, fake=False):
        print('this is the customized download function for youtube!')
        code = 1
        print(self.get_options())
        youtubedl = CustomYoutubeDL if self.is_video else ThumbnailEditedYoutubeDL
        with youtubedl(self.get_options()) as ytdl_obj:
            print('downloading:')
            if fake:
                code = 0
            elif self.info_file_path:
                code = ytdl_obj.download_with_info_file(self.info_file_path)
            else:
                self.info = ytdl_obj.extract_info(self.url, download=True)
                if self.info:
                    code = 0
            print('file downloaded successfully')
            return code, self.info, ytdl_obj


class InstagramDownloader(YoutubeDownloader):
    extractor = 'instagram'

def delete_copies(arr):
    new_list = []
    for i in arr:
        if i not in new_list:
            new_list.append(i)
    return new_list
