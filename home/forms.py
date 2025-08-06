from django import forms


class URLForm(forms.Form):
    # video format pattern
    # [type] [file extension] [resolution(height by p)] [aspect ratio] [frame rate]
    # audio format pattern
    # [type] [file extension] [audio bitrate(kbps)]
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
        'wav 128kbps': 'WAV 128kbps',
        'wav 320kbps': 'WAV 320kbps',
        'wav best': 'WAV Best Quality',
    }
    AUDIO_FORMAT_PREFIX = 'audio'
    AUDIO_FORMAT_DATA_NAMES = ['extension', 'audio_bitrate']

    CONTENT_DETAIL_CHOICES = {
        'VIDEO': {'video' + ' ' + k: v for k, v in VIDEO_FORMATS.items()},
        'AUDIO': {'audio' + ' ' + k: v for k, v in AUDIO_FORMATS.items()},
    }
    url = forms.CharField(max_length=400)
    detail = forms.ChoiceField(choices=CONTENT_DETAIL_CHOICES, initial='mp4 360p')

    def get_detail_dict(self):
        detail_str = self.cleaned_data.get('detail')
        values_list = detail_str.split(' ')
        detail_dict = dict()
        if self.VIDEO_FORMAT_PREFIX in values_list:
            detail_dict = make_detail_dict(self.VIDEO_FORMAT_DATA_NAMES, values_list)
        else:
            detail_dict = make_detail_dict(self.AUDIO_FORMAT_DATA_NAMES, values_list)
        return detail_dict


def make_detail_dict(keys: list, values: list):
    detail_dict = dict()
    if 'type' not in keys:
        keys.insert(0, 'type')
    values_length = len(values)
    for i in range(len(keys)):
        detail_dict.setdefault(keys[i])
        if i < values_length:
            detail_dict[keys[i]] = values[i]
    return detail_dict









