from django.shortcuts import render
from django.http import FileResponse
from django.forms.models import model_to_dict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult
from downloader.main_downloader import DownloadProcessError
from downloader.tasks import async_process_url, async_download_content
from downloader.models import Content
from .serializers import URLDetailSerializer, ContentInfoSerializer

# Create your views here.


class GetContentInfoAPIView(APIView):
    serializer_class = ContentInfoSerializer

    def get(self, request, *args, data=None, **kwargs):
        data = data if data else request.query_params
        serializer = URLDetailSerializer(data=data)
        if serializer.is_valid():
            process_url_result = async_process_url.delay(serializer.validated_data['url'], detail=serializer.validated_data)
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
                        'duration_string': info.get('duration_string'),
                        'thumbnail_url': info.get('thumbnail'),
                        'webpage_url_domain': info.get('webpage_url_domain'),
                        'upload_date_string': info.get('upload_date'),
                        'description': make_short_description(info.get('description'), 500),
                        'track': info.get('track'),
                        'artist': info.get('artist'),
                        'album': info.get('album'),
                        'release_date_string': info.get('release_date'),
                        'channel': info.get('channel'),
                        'uploader': info.get('uploader'),
                    }
                    content_info_serializer = ContentInfoSerializer(data=content_info_data)
                    if content_info_serializer.is_valid():
                        download_content_result = async_download_content.delay(
                            serializer.validated_data['url'], detail=serializer.validated_data, info=info,
                            info_file_path=info.get('info_file_path'), pre_created_content_obj=content.pk
                        )
                        content.celery_download_task_id = download_content_result.task_id
                        content.save()
                        return Response(content_info_serializer.data)
                    else:
                        return Response(content_info_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response("Could not extract the content info of given url!", status=status.HTTP_502_BAD_GATEWAY)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, data=request.POST, **kwargs)


class DownloadContentAPIView(APIView):

    def get(self, request, pk, *args, **kwargs):
        try:
            content = Content.objects.valid_contents().get(pk=pk)
        except Content.DoesNotExist:
            return Response("There is no such content!", status=status.HTTP_404_NOT_FOUND)

        if content.celery_download_task_id:
            download_result = AsyncResult(id=content.celery_download_task_id)
        else:
            detail_fields = ['type', 'extension', 'resolution', 'frame_rate', 'aspect_ratio', 'bitrate']
            content_detail = {k: v for k, v in model_to_dict(content).items() if k in detail_fields}
            download_result = async_download_content.delay(
                content.url, detail=content_detail, info=content.info, info_file_path=content.info_file_path,
                pre_created_content_obj=content.pk
            )
        try:
            result = download_result.get()
        except DownloadProcessError as error:
            return Response(str(error), status=status.HTTP_502_BAD_GATEWAY)
        else:
            if download_result.successful():
                content.refresh_from_db()
                if content.download_path and content.downloaded_successfully:
                    return FileResponse(open(content.download_path, 'rb'), as_attachment=True)
            return Response("Download process was unsuccessful!", status=status.HTTP_502_BAD_GATEWAY)

    def post(self, request, pk, *args, **kwargs):
        return self.get(request, pk, *args, **kwargs)


def make_short_description(description, max_len=500):
    if isinstance(description, str) and len(description) > max_len:
        return description[:max_len - 10] + '...'
    else:
        return description
