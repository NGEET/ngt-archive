from archive_api.models import DataSet, MeasurementVariable, Site, Person, Plot
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


class DataSetSerializer(serializers.HyperlinkedModelSerializer):
    """

        DataSet serializer that converts models.DataSet

    """
    created_by = serializers.ReadOnlyField(source='created_by.username')
    modified_by = serializers.ReadOnlyField(source='modified_by.username')
    submission_contact = SubmissionContactField(source='created_by', read_only=True)
    submission_date = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()

    class Meta:
        model = DataSet
        fields = ('url', 'name', 'status', 'description', 'status_comment',
                  'doi', 'start_date', 'end_date', 'qaqc_status', 'qaqc_method_description',
                  'ngee_tropics_resources', 'funding_organizations', 'doe_funding_contract_numbers',
                  'acknowledgement', 'reference', 'additional_reference_information',
                  'access_level', 'additional_access_information', 'submission_contact',
                  'submission_date', 'contact', 'sites', 'authors', 'plots', 'variables',
                  'created_by', 'created_date', 'modified_by', 'modified_date')
        readonly_fields = (
            'url', 'created_by', 'created_date', 'modified_by', 'modified_date', 'status', 'submission_contact',
            'submission_date')

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
                          'ngee_tropics_resources', 'funding_organizations',
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
