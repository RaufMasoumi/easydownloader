from django.shortcuts import render
from django.http import FileResponse
from django.forms.models import model_to_dict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiTypes
from downloader.main_downloader import DownloadProcessError
from downloader.tasks import async_process_url, async_download_content
from downloader.models import Content
from .serializers import URLDetailSerializer, ContentInfoSerializer


# Create your views here.

class GetContentInfoAPIView(APIView):

    @extend_schema(
        operation_id='api_getinfo_get',
        parameters=[
            OpenApiParameter(
                name="url",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="The URL of the content to download."
            ),
            OpenApiParameter(
                name="type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                default="audio",
                enum=["video", "audio"],
                description="The type of content to download."
            ),
            OpenApiParameter(
                name="extension",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                default="mp3",
                enum=["mp4", "mkv", "mov", "mp3", "aac", "wav"],
                description="The output file format of the downloaded content."
            ),
            OpenApiParameter(
                name="resolution",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                default=360,
                description="Resolution of the video content (as pixels). Better to pass from the list [144, 240, 360, 480, 720, 1080]."
            ),
            OpenApiParameter(
                name="frame_rate",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Frame rate of the video content (as fps)."
            ),
            OpenApiParameter(
                name="audio_bitrate",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                default=400,
                description="Bitrate of the audio content."
            ),
        ],
        request=URLDetailSerializer,
        responses={
            200: ContentInfoSerializer,
            400: OpenApiResponse(response=OpenApiTypes.STR, description="Invalid query params"),
            502: OpenApiResponse(response=OpenApiTypes.STR, description="Any problem during info extraction process")
        },
        description="Get info of the given URL",
    )
    def get(self, request, *args, data=None, **kwargs):
        data = data if data else request.query_params
        url_detail_serializer = URLDetailSerializer(data=data)
        if url_detail_serializer.is_valid():
            process_url_result = async_process_url.delay(url_detail_serializer.validated_data['url'], detail=url_detail_serializer.validated_data)
            try:
                result = process_url_result.get()
            except DownloadProcessError as error:
                return Response(str(error), status=status.HTTP_502_BAD_GATEWAY)
            else:
                if process_url_result.successful():
                    code, info, content_pk = result
                    content = Content.objects.get(pk=content_pk)
                    content_info_data = {
                        'pk': content.pk,
                        'url': info.get('original_url') or info.get('webpage_url'),
                        'title': info.get('title'),
                        'duration': info.get('duration_string'),
                        'thumbnail_url': info.get('thumbnail'),
                        'webpage_url_domain': info.get('webpage_url_domain'),
                        'upload_date': info.get('upload_date'),
                        'description': make_short_description(info.get('description'), 500),
                        'track': info.get('track'),
                        'artist': info.get('artist'),
                        'album': info.get('album'),
                        'release_date': info.get('release_date'),
                        'channel': info.get('channel'),
                        'uploader': info.get('uploader'),
                    }
                    content_info_serializer = ContentInfoSerializer(data=content_info_data)
                    if content_info_serializer.is_valid():
                        print(url_detail_serializer.validated_data)
                        download_content_result = async_download_content.delay(
                            url_detail_serializer.validated_data['url'], detail=url_detail_serializer.validated_data, info=info,
                            info_file_path=info.get('info_file_path'), pre_created_content_obj=content.pk
                        )
                        content.celery_download_task_id = download_content_result.task_id
                        content.save()
                        return Response(content_info_serializer.data, status=status.HTTP_200_OK)
                    else:
                        return Response(content_info_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response("Could not extract the content info of given url!", status=status.HTTP_502_BAD_GATEWAY)
        else:
            return Response(url_detail_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="api_getinfo_post",
        request=URLDetailSerializer,
        responses={
            200: ContentInfoSerializer,
            400: OpenApiResponse(response=OpenApiTypes.STR, description="Invalid query params"),
            502: OpenApiResponse(response=OpenApiTypes.STR, description="Any problem during info extraction process")
        },
        description="Get info of the given URL"
    )
    def post(self, request, *args, **kwargs):
        return self.get(request, *args, data=request.POST, **kwargs)


class DownloadContentAPIView(APIView):

    @extend_schema(
        operation_id="api_download_get",
        responses={
            200: OpenApiResponse(response=OpenApiTypes.BINARY, description='Downloaded content stream'),
            404: OpenApiResponse(response=OpenApiTypes.STR, description='Not found content'),
            502: OpenApiResponse(response=OpenApiTypes.STR, description='Any problem during download process')
        },
        description="Get the downloaded content. Waits until the download process ends or starts the download process.",
    )
    def get(self, request, pk, *args, **kwargs):
        try:
            content = Content.objects.valid_contents().get(pk=pk)
        except Content.DoesNotExist:
            return Response("There is no such content!", status=status.HTTP_404_NOT_FOUND)
        # add else here?
        if content.celery_download_task_id:
            download_result = AsyncResult(id=content.celery_download_task_id)
        else:
            detail_fields = ['type', 'extension', 'resolution', 'frame_rate', 'aspect_ratio', 'bitrate']
            content_detail = {k: v for k, v in model_to_dict(content).items() if k in detail_fields}
            download_result = async_download_content.delay(
                content.url, detail=content_detail, info_file_path=content.info_file_path,
                pre_created_content_obj=content.pk
            )
            content.celery_download_task_id = download_result.task_id
            content.save()
        try:
            result = download_result.get()
        except DownloadProcessError as error:
            return Response(str(error), status=status.HTTP_502_BAD_GATEWAY)
        else:
            if download_result.successful():
                content.refresh_from_db()
                if content.download_path and content.downloaded_successfully:
                    return FileResponse(open(content.download_path, 'rb'), as_attachment=True, status=status.HTTP_200_OK)
            return Response("Download process was unsuccessful!", status=status.HTTP_502_BAD_GATEWAY)

    @extend_schema(
        operation_id="api_download_post",
        responses={
            200: OpenApiResponse(response=OpenApiTypes.BINARY, description='Downloaded content stream'),
            404: OpenApiResponse(response=OpenApiTypes.STR, description='Not found content'),
            502: OpenApiResponse(response=OpenApiTypes.STR, description='Any problem during download process')
        },
        description="Get the downloaded content. Waits until the download process ends or starts the download process."
    )
    def post(self, request, pk, *args, **kwargs):
        return self.get(request, pk, *args, **kwargs)


def make_short_description(description, max_len=500):
    if isinstance(description, str) and len(description) > max_len:
        return description[:max_len - 10] + '...'
    else:
        return description
