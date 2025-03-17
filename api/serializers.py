from rest_framework import serializers
from downloader.models import Content

class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ['id', 'url', 'title', 'download_path', 'download_url']


class URLSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=400)
    detail = serializers.DictField(required=False)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

class ContentDownloadDetailSerializer(serializers.Serializer):
    TYPE_CHOICES = (
        ('video', 'video'),
        ('audio', 'audio'),
    )

    type = serializers.ChoiceField(choices=TYPE_CHOICES)
    resolution = serializers.CharField(required=False)
    frame_rate = serializers.CharField(required=False)
    extension = serializers.CharField(required=False)
    aspect_ratio = serializers.CharField(required=False)
    bitrate = serializers.CharField(required=False)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

class ContentInfoSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=400)
    title = serializers.CharField(max_length=300)
    duration = serializers.TimeField(format='%H:%M:%S')
    thumbnail = serializers.ImageField()
    webpage_url_domain = serializers.URLField(max_length=300)
    file_size = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, max_length=500)
    track = serializers.CharField(required=False, max_length=300)
    artist = serializers.CharField(required=False, max_length=300)
    album = serializers.CharField(required=False, max_length=300)
    release_date = serializers.DateTimeField(required=False, format='%Y-%m-%d')
    channel = serializers.CharField(required=False, max_length=300)
    uploader = serializers.CharField(required=False, max_length=300)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class ContentDownloadSerializer(serializers.Serializer):
    download_file = serializers.FileField()

