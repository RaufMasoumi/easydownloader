from django.urls import path
from .views import DownloadContentView

urlpatterns = [
    path('<uuid:pk>/', DownloadContentView.as_view(), name='download-content'),
]