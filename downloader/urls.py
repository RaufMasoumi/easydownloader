from django.urls import path
from .views import DownloadedContentResponseView

urlpatterns = [
    path('<uuid:pk>/', DownloadedContentResponseView.as_view(), name='download')
]