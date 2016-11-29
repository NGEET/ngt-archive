# Create your views here.
import archive_api
from archive_api.models import DataSet, MeasurementVariable, Site, Person, Plot
from archive_api.serializers import DataSetSerializer, MeasurementVariableSerializer, SiteSerializer, PersonSerializer, \
    PlotSerializer
from django.utils import timezone
from rest_framework import permissions
from rest_framework import status
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


class HasGroupPermissionOrReadonly(permissions.BasePermission):
    """
       Object-level permission to only allow owners of an object to edit it.
       Assumes the model instance has an `owner` attribute.
    """

    DRAFT = archive_api.models.STATUS_CHOICES[0][0]
    SUBMITTED = archive_api.models.STATUS_CHOICES[1][0]
    APPROVED = archive_api.models.STATUS_CHOICES[2][0]

    def has_object_permission(self, request, view, obj):

        path_info = request.path_info
        action = None
        if "/submit" in path_info:
            action = "submit"
        elif "/unsubmit" in path_info:
            action = "unsubmit"
        elif "/unapprove" in path_info:
            action = "unapprove"
        elif "/approve" in path_info:
            action = "approve"

        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS and request.user.is_authenticated:
            if not action:
                return True

        # Only Authenticated users my edit a dataset
        if request.user.is_authenticated:
            # Owner is either editing or submitting a draft
            if request.method == "DELETE":
                if obj.status == self.DRAFT:
                    return request.user.has_perm('archive_api.delete_draft_dataset')
                elif obj.status == self.SUBMITTED:
                    return request.user.has_perm('archive_api.delete_submitted_dataset')
            elif obj.status == self.DRAFT and \
                    request.user.has_perm('archive_api.edit_draft_dataset') \
                    and (action is None or action == "submit"):
                return obj.created_by == request.user or request.user.groups.filter(name='NGT Administrator').exists()
            # Administrator is approving a submitted draft, the dataset meta data
            # may not be edited at this point
            elif obj.status == self.SUBMITTED and (action is None or action == "approve"):
                return request.user.has_perm('archive_api.approve_submitted_dataset')
            elif obj.status == self.SUBMITTED and (action is None or action == "unsubmit"):
                return request.user.has_perm('archive_api.unsubmit_submitted_dataset')
            elif obj.status == self.APPROVED and (action is None or action == "unapprove"):
                return request.user.has_perm('archive_api.unapprove_approved_dataset')

        return False


class DataSetViewSet(ModelViewSet):
    """
        Returns a list of all  DataSets available to the archive_api service

    """
    permission_classes = (HasGroupPermissionOrReadonly, permissions.IsAuthenticated)
    queryset = DataSet.objects.all()
    serializer_class = DataSetSerializer
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']

    def perform_create(self, serializer):
        """
        Override the update method to update the created_by and modified by fields.
        :param serializer:
        :return:
        """
        if self.request.user.is_authenticated and serializer.is_valid():
            serializer.save(created_by=self.request.user, modified_by=self.request.user)

    def perform_update(self, serializer):
        """
        Override the update method to update the modified by fields.
        :param serializer:
        :return:
        """
        if self.request.user.is_authenticated and serializer.is_valid():
            serializer.save(modified_by=self.request.user)

    @detail_route(methods=['post', 'get'])
    def approve(self, request, pk=None):
        """
        Approve action.  Changes the dataset from 'submitted' to approved status. User must have the
        proper permissions for this action

        :param request:
        :param pk:
        :return:
        """

        self.change_status(request, HasGroupPermissionOrReadonly.APPROVED)
        return Response({'success': True, 'detail': 'DataSet has been approved.'}, status=status.HTTP_200_OK)

    @detail_route(methods=['post', 'get'])
    def unsubmit(self, request, pk=None):
        """
        Unsubmit action.  Changes the dataset from 'submitted' to draft status. User must have the
        proper permissions for this action

        :param request:
        :param pk:
        :return:
        """

        self.change_status(request, HasGroupPermissionOrReadonly.DRAFT)
        return Response({'success': True, 'detail': 'DataSet has been unsubmitted.'}, status=status.HTTP_200_OK)

    @detail_route(methods=['post', 'get'])
    def unapprove(self, request, pk=None):
        """
        Unapprove action.  Changes the dataset from 'approved' to submitted status. User must have the
        proper permissions for this action

        :param request:
        :param pk:
        :return:
        """

        self.change_status(request, HasGroupPermissionOrReadonly.SUBMITTED)
        return Response({'success': True, 'detail': 'DataSet has been unapproved.'}, status=status.HTTP_200_OK)

    @detail_route(methods=['post', 'get'])
    def submit(self, request, pk=None):
        """
        Submit action. Changes the dataset from 'draft' to 'submitted' status. User must have
        the proper permissions for this action.

        :param request:
        :param pk:
        :return:
        """
        self.change_status(request, HasGroupPermissionOrReadonly.SUBMITTED)
        return Response({'success': True, 'detail': 'DataSet has been submitted.'}, status=status.HTTP_200_OK)

    def change_status(self, request, status):
        """
        Change the status of the dataset. This will raise and exception on ValidationErrors and
        invalid permissions.
        :param request:
        :param status:
        :return:
        """
        dataset = self.get_object()  # this will initiate a permissions check
        dataset.status = status
        dataset.submission_date = timezone.now()
        serializer = DataSetSerializer(dataset, context={'request': request})
        deserializer = DataSetSerializer(dataset, data=serializer.data, context={'request': request})
        deserializer.is_valid(raise_exception=True)
        self.perform_update(deserializer)


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


class PersonViewSet(ModelViewSet):
    """
        Returns a list of all  Persons available to the archive_api service

    """
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    http_method_names = ['get', 'post', 'put', 'head', 'options']


class PlotViewSet(ModelViewSet):
    """
        Returns a list of all Plots available to the archive_api service

    """
    queryset = Plot.objects.all()
    serializer_class = PlotSerializer
    http_method_names = ['get', 'head', 'options']
