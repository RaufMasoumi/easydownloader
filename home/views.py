from django.shortcuts import render, reverse, get_object_or_404
from django.urls import reverse_lazy
from django.http import FileResponse
from django.views.generic import FormView
from downloader.main_downloader import download_content, DownloadProcessError
from downloader.tasks import async_process_url, async_download_content
from downloader.views import DownloadedContentResponseView
from downloader.models import Content
from api.views import make_short_description
from .forms import URLForm
# Create your views here.


class ProcessURLFormView(FormView):
    form_class = URLForm
    success_url = reverse_lazy('home')
    template_name = 'home/home.html'

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
        process_url_result = async_process_url.delay(url=form.cleaned_data['url'], detail=form.cleaned_data['detail'])
        try:
            code, info, content_pk = process_url_result.get()
        except DownloadProcessError as error:
            context['successful_process'] = False
            context['error_message'] = str(error)
        else:
            content = get_object_or_404(Content.objects.valid_contents(), pk=content_pk)
            content_info = {
                'pk': content_pk,
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
            download_result = async_download_content.delay(
                url=form.cleaned_data['url'], detail=form.cleaned_data['detail'], pre_created_content_obj=content.pk, info=info,
                info_file_path=content.info_file_path
            )
            content.celery_download_task_id = download_result.task_id
            content.save()
            context['successful_process'] = True
            context['content_info'] = content_info
        return self.render_to_response(context)

    # def form_invalid(self, form):
    #     context = self.get_context_data()
    #     context['valid_link'] = False
    #     # permanent! this will raise errors about the wrong link or unsuccessful download process.
    #     return self.render_to_response(context)


class HomeView(ProcessURLFormView):
    template_name = 'home/home.html'
    success_url = reverse_lazy('home')
