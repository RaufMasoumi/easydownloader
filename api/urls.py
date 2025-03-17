from django.urls import path
from .views import ContentInfoAPIView, GetDownloadableContentAPIView


urlpatterns = [
    path('info/', ContentInfoAPIView.as_view(), name='info'),
    path('download/<uuid:pk>/', GetDownloadableContentAPIView.as_view(), name='get-downloadable-content-api'),
    # path('info/', GetContentInfoAPIView.as_view(), name='get-content-info-api'),
]