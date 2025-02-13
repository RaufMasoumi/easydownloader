from django import forms


class LinkForm(forms.Form):
    # video format pattern
    # [type] [file extension] [resolution(height by p)] [aspect ratio] [frame rate]
    # audio format pattern
    # [type] [file extension] [bitrate(kbps)]
    # Do not forget to put spaces between fields because the choice will be splitted by spaces.
    # write none for the fields that don't want to change. (no needed for the fields after last set field but preferred)

    VIDEO_FORMATS = {
        'mp4 worst': 'MP4 Worst Quality',
        'mp4 144p': 'MP4 144p',
        'mp4 240p': 'MP4 240p',
        'mp4 360p': 'MP4 360p',
        'mp4 480p': 'MP4 480p',
        'mp4 720p': 'MP4 720p (HD)',
        'mp4 1080p': 'MP4 1080p (Full HD)',
        'mp4 1080p none 60fps': 'MP4 1080p (Full HD)',
        'mp4 best': 'MP4 Best Quality',
        'mkv worst': 'MKV Worst Quality',
        'mkv 144p': 'MKV 144p',
        'mkv 240p': 'MKV 240p',
        'mkv 360p': 'MKV 360p',
        'mkv 480p': 'MKV 480p',
        'mkv 720p': 'MKV 720p (HD)',
        'mkv 1080p': 'MKV 1080p (Full HD)',
    }
    VIDEO_FORMAT_PREFIX = 'video'
    VIDEO_FORMAT_DATA_NAMES = ['extension', 'resolution', 'aspect_ratio', 'frame_rate']

    AUDIO_FORMATS = {
        'mp3 128kbps': 'MP3 128kbps',
        'mp3 320kbps': 'MP3 320kbps',
        'mp3 best': 'MP3 Best Quality',
        'wav 16bit': 'WAV 16bit',
        'wav 24bit': 'WAV 24bit',
        'wav best': 'WAV Best Quality',
    }
    AUDIO_FORMAT_PREFIX = 'audio'
    AUDIO_FORMAT_DATA_NAMES = ['extension', 'bitrate']

    CONTENT_DETAIL_CHOICES = {
        'VIDEO': {'video' + ' ' + k: v for k, v in VIDEO_FORMATS.items()},
        'AUDIO': {'audio' + ' ' + k: v for k, v in AUDIO_FORMATS.items()},
    }
    link = forms.CharField(max_length=400)
    format = forms.ChoiceField(choices=CONTENT_DETAIL_CHOICES, initial='mp4 360p')

    # def translate_format(self, default='bestvideo*/best'):
    #     translated_format = default
    #     try:
    #         format_string = self.cleaned_data['format']
    #     except AttributeError:
    #         return translated_format
    #     else:
    #         format_data_list = format_string.split(' ')
    #         if format_data_list[0] == self.VIDEO_FORMAT_PREFIX:
    #             format_data = make_format_data_dict(self.VIDEO_FORMAT_DATA_NAMES, format_data_list)
    #         else:
    #             format_data = make_format_data_dict(self.AUDIO_FORMAT_DATA_NAMES, format_data_list)
    #         translated_format =

def make_format_data_dict(keys: list, values: list):
    format_data_dict = dict()
    keys.insert(0, 'type')
    values_length = len(values)
    for i in range(len(keys)):
        format_data_dict.setdefault(keys[i])
        if i < values_length:
            format_data_dict[keys[i]] = values[i]
    return format_data_dict









