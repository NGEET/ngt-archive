from urllib.parse import urlparse

from archive_api.models import DataSet, MeasurementVariable, Site, Person, Plot, Author
from django.core.urlresolvers import resolve
from django.db import transaction
from rest_framework import serializers


class SubmissionContactField(serializers.JSONField):
    """
    The submission contact for an entity owner (auth.User) should be
    displayed with first, last and email
    """

    def to_representation(self, obj):
        return {'first_name': obj.first_name,
                'last_name': obj.last_name,
                'email': obj.email}

    def to_internal_value(self, data):
        return {'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data['email']}


class AuthorsField(serializers.SerializerMethodField):
    """
    Author objects are serialized and deserialized for reading and writing
    """

    def __init__(self, **kwargs):
        super(AuthorsField, self).__init__(**kwargs)

        self.read_only = False

    def to_internal_value(self, data):
        authors = []
        for author in data:
            path = urlparse(author).path
            resolved_func, __, resolved_kwargs = resolve(path)
            person = resolved_func.cls.queryset.get(pk=resolved_kwargs['pk'])
            authors.append(person)

        return {'authors': authors}


class DataSetSerializer(serializers.HyperlinkedModelSerializer):
    """

        DataSet serializer that converts models.DataSet

    """
    created_by = serializers.ReadOnlyField(source='created_by.username')
    modified_by = serializers.ReadOnlyField(source='modified_by.username')
    submission_contact = SubmissionContactField(source='created_by', read_only=True)
    submission_date = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()
    authors = AuthorsField()

    def get_authors(self, instance):
        """
        Serialize the authors.  This should be an ordered list  of authors
        :param instance:
        :return:
        """
        author_order = Author.objects \
            .filter(dataset_id=instance.id) \
            .order_by('order')

        authors = [a.author for a in author_order]

        # Return a list of person urls
        serializers = PersonSerializer(authors, many=True, context={'request': self.context['request']}).data
        return [p["url"] for p in serializers]

    class Meta:
        model = DataSet
        fields = ('url', 'data_set_id', 'name', 'version', 'status', 'description', 'status_comment',
                  'doi', 'start_date', 'end_date', 'qaqc_status', 'qaqc_method_description',
                  'ngee_tropics_resources', 'funding_organizations', 'doe_funding_contract_numbers',
                  'acknowledgement', 'reference', 'additional_reference_information',
                  'access_level', 'additional_access_information', 'originating_institution', 'submission_contact',
                  'submission_date', 'contact', 'sites', 'authors', 'plots', 'variables',
                  'created_by', 'created_date', 'modified_by', 'modified_date')
        readonly_fields = (
            'url', 'version', 'created_by', 'created_date', 'modified_by', 'modified_date', 'status',
            'submission_contact',
            'submission_date', 'data_set_id')

    def validate(self, data):
        """
        Validate the fields.
        """
        errors = dict()
        if {'start_date', 'end_date'}.issubset(data.keys()) and data['start_date'] and data['end_date'] and data[
            'start_date'] > data['end_date']:
            raise serializers.ValidationError("start_date must come before end_date")
        # If the dataset is approved or submitted there are an extra set of fields
        # that are required
        if self.instance and self.instance.status in ['1', '2']:
            for field in ['sites', 'authors', 'name', 'description', 'contact', 'variables',
                          'ngee_tropics_resources', 'funding_organizations', 'originating_institution',
                          'access_level']:  # Check for required fields
                if field in data.keys():
                    if not data[field]:
                        errors.setdefault('missingRequiredFields', [])
                        errors['missingRequiredFields'].append(field)
                else:
                    errors.setdefault('missingRequiredFields', [])
                    errors['missingRequiredFields'].append(field)

        if len(errors) > 0:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):

        # Use an atomic transaction for managing dataset and authors
        with transaction.atomic():
            # Pop off authors data, if exists
            author_data = []
            if "authors" in validated_data.keys():
                author_data = validated_data.pop('authors')

            # Create dataset first
            dataset = DataSet.objects.create(**validated_data)
            dataset.clean()
            dataset.save()

            # save the author data
            self.add_authors(author_data, dataset)

        return dataset

    def update(self, instance, validated_data):

        # Use an atomic transaction for managing dataset and authors
        with transaction.atomic():
            # pop off the authors data
            if "authors" in validated_data.keys():
                author_data = validated_data.pop('authors')

                # remove the existing authors
                Author.objects.filter(dataset_id=instance.id).delete()  # delete first
                self.add_authors(author_data, instance)

            # Update Dataset metadata
            super(self.__class__, self).update(instance=instance, validated_data=validated_data)

        return instance

    def add_authors(self, author_data, instance):
        for idx, author in enumerate(author_data):
            Author.objects.create(dataset=instance, order=idx, author=author)


class MeasurementVariableSerializer(serializers.HyperlinkedModelSerializer):
    """
        MeasurementVariable serializer that convers models.MeasurementVariable
    """

    class Meta:
        model = MeasurementVariable
        fields = '__all__'


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    """
        Site serializer that converts models.Site
    """

    class Meta:
        model = Site
        fields = '__all__'


class PersonSerializer(serializers.HyperlinkedModelSerializer):
    """
        Person serializer that converts models.Person
    """

    class Meta:
        model = Person
        fields = '__all__'


class PlotSerializer(serializers.HyperlinkedModelSerializer):
    """
        Plot serializer that converts models.Plot
    """

    class Meta:
        model = Plot
        fields = '__all__'
