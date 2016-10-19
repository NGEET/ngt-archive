from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import  ModelViewSet

from archive_api.models import DataSet
from archive_api.serializers import DataSetSerializer


class DataSetViewSet(ModelViewSet):
    """
        Returns a list of all  DataSets available to the archive_api service

    """
    queryset = DataSet.objects.all()
    serializer_class = DataSetSerializer
    http_method_names = ['get', 'post', 'put','head','options']
