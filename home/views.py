from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import FormView
from .forms import LinkForm
# Create your views here.


class ProcessLinkFormView(FormView):
    form_class = LinkForm
    success_url = reverse_lazy('home')
    template_name = 'home/home.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "GET":
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
        # permanent! this will be the process of downloading from the link.
        return self.render_to_response(context)

    def form_invalid(self, form):
        context = self.get_context_data()
        context['valid_link'] = False
        # permanent! this will raise errors about the wrong link or unsuccessful download process.
        return self.render_to_response(context)



class HomeView(ProcessLinkFormView):
    template_name = 'home/home.html'
    success_url = reverse_lazy('home')




