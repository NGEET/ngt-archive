from rest_framework import serializers

from archive_api.models import DataSet


class DataSetSerializer(serializers.HyperlinkedModelSerializer):
    """

        DataSet serializer that converts models.DataSet

    """

    class Meta:
        model = DataSet
