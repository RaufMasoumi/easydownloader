from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView, Response
from rest_framework import status
from downloader.models import Content
from home.forms import URLForm
from .serializers import ContentSerializer, URLSerializer

# Create your views here.


class ContentInfoAPIView(APIView):

    def get(self, request):
        form = URLForm(request.query_params)
        if form.is_valid():
            pass
            # target 1: extract the info of the url

            # target 2: starts the download process for better user experience

            # target 3: create a content model instance and get the pk of the instance

            # target 4: send the extracted info to the user + the content instance pk

        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        serializer = URLSerializer(data=request.data)
        if serializer.is_valid():
            pass
            # extract info and start download process
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class GetDownloadableContentAPIView(APIView):

    def get(self, request, pk):
        print('hello')
        content = get_object_or_404(Content.objects.valid_contents(), pk=pk)
        serializer = ContentSerializer(content)
        return Response(serializer.data)



