from rest_framework import serializers


class URLDetailSerializer(serializers.Serializer):
    TYPE_CHOICES = (
        ('video', 'video'),
        ('audio', 'audio'),
    )
    SUPPORTED_VIDEO_EXTENSIONS = ('mp4', 'mkv', 'mov')
    SUPPORTED_AUDIO_EXTENSIONS = ('mp3', 'aac', 'wav')
    EXTENSION_CHOICES = (
        (
            'video', tuple(((ext, ext.lower()) for ext in SUPPORTED_VIDEO_EXTENSIONS))
        ),
        (
            'audio', tuple(((ext, ext.lower()) for ext in SUPPORTED_AUDIO_EXTENSIONS))
        ),
        # ('mp4', 'mp4'),
        # ('mkv', 'mkv'),
        # ('mov', 'mov'),
        # ('mp3', 'mp3'),
        # ('aac', 'aac'),
        # ('wav', 'wav'),
    )
    url = serializers.URLField(max_length=400)
    type = serializers.ChoiceField(choices=TYPE_CHOICES, required=False, default='audio')
    extension = serializers.ChoiceField(choices=EXTENSION_CHOICES, default='mp3')
    # video related detail
    resolution = serializers.IntegerField(required=False, default=360)
    frame_rate = serializers.IntegerField(required=False)
    aspect_ratio = serializers.IntegerField(required=False)
    # audio related detail
    audio_bitrate = serializers.IntegerField(required=False, default=400)

    def validate_resolution(self, value):
        valid_resolution_range = [100, 1080]
        if value < min(valid_resolution_range) or value > max(valid_resolution_range):
            raise serializers.ValidationError('Incorrect resolution! it must be in 100-1080 range!')
        return value

    def validate_audio_bitrate(self, value):
        valid_bitrate_range = [100, 400]
        if value < min(valid_bitrate_range) or value > max(valid_bitrate_range):
            raise serializers.ValidationError('Incorrect audio bitrate! it must be in 100-400 range!')
        return value

    def validate(self, data):
        if data.get('type') == 'video':
            if data.get('extension'):
                data['extension'] = data['extension'] if data['extension'] in self.SUPPORTED_VIDEO_EXTENSIONS else 'mp4'
        else:
            if data.get('extension'):
                data['extension'] = data['extension'] if data['extension'] in self.SUPPORTED_AUDIO_EXTENSIONS else 'mp3'

        return data

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class ContentInfoSerializer(serializers.Serializer):
    pk = serializers.UUIDField()
    url = serializers.URLField(max_length=400)
    title = serializers.CharField(max_length=300)
    # duration = serializers.TimeField(format='%H:%M:%S', required=False, allow_null=True)
    duration = serializers.CharField(max_length=50)
    thumbnail_url = serializers.URLField(max_length=400)
    webpage_url_domain = serializers.CharField(max_length=300)
    file_size = serializers.CharField(max_length=100, required=False, allow_null=True)
    # upload_date = serializers.DateTimeField(format='%Y-%m-%d', required=False, allow_null=True)
    upload_date = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_null=True, max_length=500)
    track = serializers.CharField(required=False, allow_null=True, max_length=300)
    artist = serializers.CharField(required=False, allow_null=True, max_length=300)
    album = serializers.CharField(required=False, allow_null=True,  max_length=300)
    # release_date = serializers.DateTimeField(format='%Y-%m-%d', required=False, allow_null=True)
    release_date = serializers.CharField(required=False, allow_null=True, max_length=100)
    channel = serializers.CharField(required=False, allow_null=True, max_length=300)
    uploader = serializers.CharField(required=False, allow_null=True, max_length=300)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

