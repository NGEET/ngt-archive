# Create your views here.
from rest_framework.viewsets import  ModelViewSet

from archive_api.models import DataSet, MeasurementVariable, Site, Contact, Plot
from archive_api.serializers import DataSetSerializer, MeasurementVariableSerializer, SiteSerializer, ContactSerializer, \
    PlotSerializer


class DataSetViewSet(ModelViewSet):
    """
        Returns a list of all  DataSets available to the archive_api service

    """
    queryset = DataSet.objects.all()
    serializer_class = DataSetSerializer
    http_method_names = ['get', 'post', 'put','head','options']


class MeasurementVariableViewSet(ModelViewSet):
    """
        Returns a list of all  Measurement Variables available to the archive_api service

    """
    queryset = MeasurementVariable.objects.all()
    serializer_class = MeasurementVariableSerializer
    http_method_names = ['get', 'head', 'options']


class SiteViewSet(ModelViewSet):
    """
        Returns a list of all  Measurement Variables available to the archive_api service

    """
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    http_method_names = ['get', 'head', 'options']


class ContactViewSet(ModelViewSet):
    """
        Returns a list of all  Contacts available to the archive_api service

    """
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    http_method_names = ['get', 'post', 'put', 'head', 'options']


class PlotViewSet(ModelViewSet):
    """
        Returns a list of all Plots available to the archive_api service

    """
    queryset = Plot.objects.all()
    serializer_class = PlotSerializer
    http_method_names = ['get', 'head', 'options']
