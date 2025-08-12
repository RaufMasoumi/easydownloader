from django.forms import model_to_dict
from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import View, FormView
from celery.result import AsyncResult
from rest_framework import status
import os
from api.views import make_short_description
from home.forms import URLForm
from .main_downloader import DownloadProcessError
from .models import Content
from .tasks import async_process_url, async_download_content
# Create your views here.


class ProcessURLFormView(FormView):
    form_class = URLForm
    success_url = reverse_lazy('home')
    template_name = 'downloader/process_url_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "GET" and self.request.GET:
            kwargs.update(
                {
                    'data': self.request.GET,
                    'files': self.request.FILES,
                }
            )
        return kwargs

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def form_valid(self, form):
        context = self.get_context_data()
        process_url_result = async_process_url.delay(url=form.cleaned_data['url'], detail=form.get_detail_dict())
        try:
            code, info, content_pk = process_url_result.get()
        except DownloadProcessError as error:
            context['successful_process'] = False
            context['error_message'] = str(error)
        else:
            content = get_object_or_404(Content.objects.valid_contents(), pk=content_pk)
            content_info = {
                'Url': info.get('original_url') or info.get('webpage_url'),
                'Title': info.get('title'),
                'Duration': info.get('duration_string'),
                'Thumbnail Url': info.get('thumbnail'),
                'Upload Date': info.get('upload_date'),
                'Description': make_short_description(info.get('description'), 500),
                'Track': info.get('track'),
                'Artist': info.get('artist'),
                'Album': info.get('album'),
                'Release Date': info.get('release_date'),
                'Channel': info.get('channel'),
                'Uploader': info.get('uploader'),
            }
            download_result = async_download_content.delay(
                url=form.cleaned_data['url'], detail=form.get_detail_dict(), pre_created_content_obj=content.pk, info=info,
                info_file_path=content.info_file_path
            )
            content.celery_download_task_id = download_result.task_id
            content.save()
            context['content_info'] = content_info
            context['content_pk'] = content.pk
            context['successful_process'] = True
        return self.render_to_response(context)

    # def form_invalid(self, form):
    #     context = self.get_context_data()
    #     context['valid_link'] = False
    #     # permanent! this will raise errors about the wrong link or unsuccessful download process.
    #     return self.render_to_response(context)


class DownloadContentView(View):

    def get(self, request, pk, *args, **kwargs):
        content = get_object_or_404(Content.objects.valid_contents(), pk=pk)
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
            return HttpResponse(f"<h1>{str(error)}</h1>", status=status.HTTP_502_BAD_GATEWAY)
        else:
            if download_result.successful():
                content.refresh_from_db()
                if content.download_path and content.downloaded_successfully and os.path.exists(content.download_path):
                    return FileResponse(open(content.download_path, 'rb'), as_attachment=True, status=status.HTTP_200_OK)
            return HttpResponse("<h1>Download process was unsuccessful!</h1>", status=status.HTTP_502_BAD_GATEWAY)

    def post(self, request, pk, *args, **kwargs):
        return self.get(request, pk, *args, **kwargs)
