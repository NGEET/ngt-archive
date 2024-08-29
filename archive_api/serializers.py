from rest_framework.fields import RegexField, URLField
from urllib.parse import urlparse

import os

from archive_api.models import DataSet, MeasurementVariable, Site, Person, Plot, Author
from django.urls import resolve
from django.db import transaction
from rest_framework import serializers

from rest_framework.reverse import reverse


class StringToIntReadOnlyField(serializers.ReadOnlyField):
    """
    Readonly field that uses a character externally and integer internally
    """
    def to_representation(self, obj):
        return str(obj)


class StringToIntField(serializers.Field):
    """
    field that uses a character externally and integer internally
    """

    def to_internal_value(self, data):
        return int(data)

    def to_representation(self, obj):
        return str(obj)


class AuthorsField(serializers.SerializerMethodField):
    """
    Author objects are serialized and deserialized for reading and writing
    """

    def __init__(self, **kwargs):
        super(AuthorsField, self).__init__(**kwargs)

        self.read_only = False

    def to_internal_value(self, data):
        """
        Resolve person Urls into Person objects
        :param data: list of Person urls
        :type data: list
        :return: dict with 'authors' key containing a list of Person objects
        """
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
    managed_by = serializers.ReadOnlyField(source='managed_by.username')
    modified_by = serializers.ReadOnlyField(source='modified_by.username')
    archive_filename = serializers.SerializerMethodField()
    submission_date = serializers.ReadOnlyField()
    publication_date = serializers.ReadOnlyField()
    approval_date = serializers.ReadOnlyField()
    authors = AuthorsField()
    archive = serializers.SerializerMethodField()
    status = StringToIntReadOnlyField()
    qaqc_status = StringToIntField(required=False,allow_null=True)
    access_level = StringToIntField(required=False, allow_null=True)
    doi = RegexField("http(s)?://(dx.)?doi.org/10.15486/ngt/", required=False, allow_null=True, allow_blank=True)

    def get_archive_filename(self,instance):

        if instance.archive:

            base, filename = os.path.split(instance.archive.name)
            return filename
        else:
            return None

    def get_archive(self, instance):
        """ Returns the archive access url"""
        if instance.archive:
            url_kwargs = {
                'pk': instance.pk,

            }

            url = reverse('dataset-detail', kwargs=url_kwargs, request=self.context["request"])
            url += "archive/"

            return url
        return None

    def get_authors(self, instance):
        """
        Serialize the authors.  This should be an ordered list  of authors
        :param instance:
        :return:
        """

        # Get Authors in the specified order
        author_order = Author.objects \
            .filter(dataset_id=instance.id) \
            .order_by('order')

        # Put in a list
        authors = [a.author for a in author_order]

        # Return a list of person urls
        serializers = PersonSerializer(authors, many=True, context={'request': self.context['request']}).data
        return [p["url"] for p in serializers]

    class Meta:
        model = DataSet
        fields = ('url', 'data_set_id', 'name', 'version', 'status', 'citation', 'description', 'status_comment',
                  'doi', 'start_date', 'end_date', 'qaqc_status', 'qaqc_method_description',
                  'ngee_tropics_resources', 'funding_organizations', 'doe_funding_contract_numbers',
                  'acknowledgement', 'reference', 'additional_reference_information',
                  'access_level', 'additional_access_information', 'originating_institution',
                  'submission_date', 'contact', 'sites', 'authors', 'plots', 'variables', 'archive',
                  'archive_filename', 'needs_review', 'needs_approval', "is_published",
                  'managed_by', 'created_date', 'modified_by', 'modified_date'
                  , 'cdiac_import', 'cdiac_submission_contact','approval_date', 'publication_date')
        read_only_fields = ('cdiac_import', 'cdiac_submission_contact',
            'url', 'version', 'managed_by', 'created_date', 'modified_by', 'modified_date', 'status', 'archive',
            'archive_filename', 'citation', 'needs_review', 'needs_approval', "is_published",
            'submission_date', 'data_set_id','approval_date', 'publication_date')

    def validate(self, data):
        """
        Validate the fields.
        """
        errors = dict()

        # Validate the data range
        if {'start_date', 'end_date'}.issubset(data.keys()) and data['start_date'] and data['end_date'] and data[
            'start_date'] > data['end_date']:
            errors["end_date"]="Start date must come before end date"

        # Make sure description has at least 100 words
        if 'description' in data.keys() and data['description'] and len(data['description'].split()) < 100:
            errors["description"] = f"Description must be at least 100 words. Current count is {len(data['description'].split())}."

        # Validate the selected plots
        if 'plots' in data.keys():
            if 'sites' not in data.keys():
                errors.setdefault('plots', [])
                errors["plots"].append("A site must be selected.")
            else:
                for plot in data["plots"]:
                    if plot.site not in data["sites"]:
                        errors.setdefault('plots', [])
                        errors["plots"].append("Select the site corresponding to plot {}:{}".format(plot.plot_id, plot.name))

        # If the dataset is approved or submitted there are an extra set of fields
        # that are required
        if self.instance and self.instance.status > DataSet.STATUS_DRAFT:
            if not self.instance.archive:
                errors.setdefault('missingRequiredFields', [])
                errors['missingRequiredFields'].append("archive")

            for field in ['sites', 'authors', 'name', 'description', 'contact', 'variables',
                          'ngee_tropics_resources', 'originating_institution',
                          'access_level', 'qaqc_method_description']:  # Check for required fields
                if field in data.keys():
                    if data[field] is None or (isinstance(data[field], (list, tuple, str)) and not data[field]):
                        errors.setdefault('missingRequiredFields', [])
                        errors['missingRequiredFields'].append(field)
                else:
                    errors.setdefault('missingRequiredFields', [])
                    errors['missingRequiredFields'].append(field)

        if len(errors) > 0:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        """
        Override the serializer create method to handle Dataset and Author
        creation in an atomic transaction

        :param validated_data:
        :return: dataset
        """

        # Use an atomic transaction for managing dataset and authors
        with transaction.atomic():
            # Pop off authors data, if exists
            author_data = []
            sites_data = []
            plots_data = []
            variables_data = []
            if "authors" in validated_data.keys():
                author_data = validated_data.pop('authors')

            if "sites" in validated_data.keys():
                sites_data = validated_data.pop('sites')

            if "plots" in validated_data.keys():
                plots_data = validated_data.pop('plots')

            if "variables" in validated_data.keys():
                variables_data = validated_data.pop('variables')

            # Create dataset first
            dataset = DataSet.objects.create(**validated_data)
            dataset.clean()
            dataset._change_reason = f'Created Dataset Metadata'
            dataset.save()

            # save the author data
            reasons = set()
            if len(author_data) > 0:
                reasons.add("authors")
                self.add_authors(author_data, dataset)
            for obj in sites_data:
                reasons.add("sites")
                dataset.sites.add(obj)
            for obj in plots_data:
                reasons.add("plots")
                dataset.plots.add(obj)
            for obj in variables_data:
                reasons.add("variables")
                dataset.variables.add(obj)

            if len(reasons) > 0:
                dataset._change_reason = f'Added {", ".join(reasons)}'
                dataset.save()

        return dataset

    def update(self, instance, validated_data):
        """
       Override the serializer update method to handle Dataset and Author
       update in an atomic transaction

       :param validated_data:
       :return: dataset
       """

        # Use an atomic transaction for managing dataset and authors
        with transaction.atomic():
            # pop off the authors data
            if "authors" in validated_data.keys():
                author_data = validated_data.pop('authors')

                instance._change_reason = 'Adding Authors to  Dataset Metadata'
                # remove the existing authors
                Author.objects.filter(dataset_id=instance.id).delete()  # delete first
                self.add_authors(author_data, instance)

            instance._change_reason = 'Update Dataset Metadata'

            # Update Dataset metadata
            super(self.__class__, self).update(instance=instance, validated_data=validated_data)

        return instance

    def add_authors(self, author_data, instance):
        """
        Enumerate over author data and create ordered author objects

        :param author_data: Person objects
        :type author_data: list
        :param instance: dataset to add authors to
        :type instance: DataSet
        """
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
        fields = ('url', 'first_name', 'last_name', 'email', 'institution_affiliation', 'orcid')


class PlotSerializer(serializers.HyperlinkedModelSerializer):
    """
        Plot serializer that converts models.Plot
    """

    class Meta:
        model = Plot
        fields = '__all__'
