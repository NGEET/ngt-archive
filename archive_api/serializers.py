from rest_framework import serializers

from archive_api.models import DataSet, MeasurementVariable, Site, Contact, Plot


class DataSetSerializer(serializers.HyperlinkedModelSerializer):
    """

        DataSet serializer that converts models.DataSet

    """

    class Meta:
        model = DataSet


class MeasurementVariableSerializer(serializers.HyperlinkedModelSerializer):
    """
        MeasurementVariable serializer that convers models.MeasurementVariable
    """

    class Meta:
        model = MeasurementVariable


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    """
        Site serializer that converts models.Site
    """

    class Meta:
        model = Site


class ContactSerializer(serializers.HyperlinkedModelSerializer):
    """
        Site serializer that converts models.Site
    """

    class Meta:
        model = Contact


class PlotSerializer(serializers.HyperlinkedModelSerializer):
    """
        Site serializer that converts models.Site
    """

    class Meta:
        model = Plot
