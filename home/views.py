from django.urls import reverse_lazy
from downloader.views import ProcessURLFormView
# Create your views here.


class HomeView(ProcessURLFormView):
    template_name = 'home/home.html'
    success_url = reverse_lazy('home')
