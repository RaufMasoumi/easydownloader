from django.shortcuts import render, reverse
from django.urls import reverse_lazy
from django.http import FileResponse
from django.views.generic import FormView
from downloader.main_downloader import download_content
from downloader.views import DownloadedContentResponseView
from .forms import URLForm
# Create your views here.


class ProcessLinkFormView(FormView):
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
        context['valid_link'] = True
        info = download_content(form.cleaned_data['link'])
        context['successful_process'] = True
        # context['download_url'] = reverse('download')
        return self.render_to_response(context)

    def form_invalid(self, form):
        context = self.get_context_data()
        context['valid_link'] = False
        # permanent! this will raise errors about the wrong link or unsuccessful download process.
        return self.render_to_response(context)


class HomeView(ProcessLinkFormView):
    template_name = 'home/home.html'
    success_url = reverse_lazy('home')
