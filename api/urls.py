from django.urls import path
from .views import GetContentInfoAPIView, DownloadContentAPIView


urlpatterns = [
    path('getinfo/', GetContentInfoAPIView.as_view(), name='get-content-info-api'),
    path('download/<uuid:pk>/', DownloadContentAPIView.as_view(), name='download-content-api'),
]