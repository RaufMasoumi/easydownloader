from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, HttpResponseNotFound
from django.views.generic import View
from .models import Content
# Create your views here.


class DownloadedContentResponseView(View):

    def get(self, request, pk, **kwargs):
        content = get_object_or_404(Content, pk=pk)
        if content.download_url:
            return redirect(content.download_url)
        elif content.download_path:
            try:
                file = open(content.download_path, 'rb')
            except FileNotFoundError:
                return HttpResponseNotFound('There is no correct data for the content to download!')
            else:
                return FileResponse(file, as_attachment=True, filename=content.download_path)
        else:
            return HttpResponseNotFound('There is no data for the content to download!')

    def post(self, request, pk, **kwargs):
        return self.get(request, pk, **kwargs)
