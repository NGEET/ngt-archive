# Create your views here.
import os
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.utils.encoding import smart_str
from rest_framework import permissions
from rest_framework import status
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

import archive_api
from archive_api.models import DataSet, MeasurementVariable, Site, Person, Plot
from archive_api.serializers import DataSetSerializer, MeasurementVariableSerializer, SiteSerializer, PersonSerializer, \
    PlotSerializer

DRAFT = archive_api.models.STATUS_CHOICES[0][0]
SUBMITTED = archive_api.models.STATUS_CHOICES[1][0]
APPROVED = archive_api.models.STATUS_CHOICES[2][0]

PRIVATE = archive_api.models.ACCESS_CHOICES[0][0]
NGEET = archive_api.models.ACCESS_CHOICES[1][0]
PUBLIC = archive_api.models.ACCESS_CHOICES[2][0]


class HasArchivePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        path_info = request.path_info
        if "/archive" not in path_info:
            return False

        if request.user.groups.filter(name='NGT Administrator').exists():
            return True # Admin always has access
        elif obj.access_level == PRIVATE:
            return obj.created_by == request.user # owner always has access
        elif obj.access_level == NGEET:
            return request.user.groups.filter(name='NGT User').exists() # All NGT User has access
        else:
            # This is public, All have access
            return True


class HasSubmitPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        path_info = request.path_info
        if "/submit" not in path_info:
            return False

        if obj.status != DRAFT:
            if obj.created_by == request.user or request.user.groups.filter(name='NGT Administrator').exists():
                raise PermissionDenied(detail='Only a data set in DRAFT status may be submitted')
        elif obj.status == DRAFT and \
                request.user.has_perm('archive_api.edit_draft_dataset'):
            return obj.created_by == request.user or request.user.groups.filter(name='NGT Administrator').exists()

        return False


class HasApprovePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        path_info = request.path_info
        if "/approve" not in path_info:
            return False

        if request.user.has_perm('archive_api.approve_submitted_dataset'):
            if obj.status != SUBMITTED:
                raise PermissionDenied(detail='Only a data set in SUBMITTED status may be approved')
            elif obj.status == SUBMITTED:
                return request.user.has_perm('archive_api.approve_submitted_dataset')

        return False


class HasUnsubmitPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        path_info = request.path_info
        if "/unsubmit" not in path_info:
            return False

        if request.user.has_perm('archive_api.unsubmit_submitted_dataset'):
            if obj.status != SUBMITTED:
                raise PermissionDenied(detail='Only a data set in SUBMITTED status may be un-submitted')

            elif obj.status == SUBMITTED:
                return True

        return False


class HasUnapprovePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        path_info = request.path_info
        if "/unapprove" not in path_info:
            return False

        if request.user.has_perm('archive_api.unapprove_approved_dataset'):
            if obj.status != APPROVED:
                raise PermissionDenied(detail='Only a data set in APPROVED status may be unapproved')

            if obj.status == APPROVED:
                return True

        return False


class HasUploadPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        path_info = request.path_info
        if "/upload" not in path_info:
            return False

        if obj.status == DRAFT and \
                request.user.has_perm('archive_api.edit_draft_dataset'):
            return obj.created_by == request.user or request.user.groups.filter(name='NGT Administrator').exists()

        return False


class HasEditPermissionOrReadonly(permissions.BasePermission):
    """
       Object-level permission to only allow owners of an object  or administrators to edit it.
       Assumes the model instance has an `created_by` attribute.
    """

    def has_object_permission(self, request, view, obj):

        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Owner is either editing or submitting a draft
        if request.method == "DELETE":
            if obj.status == DRAFT:
                return request.user.has_perm('archive_api.delete_draft_dataset')
            elif obj.status == SUBMITTED:
                return request.user.has_perm('archive_api.delete_submitted_dataset')
        elif obj.status == DRAFT and \
                request.user.has_perm('archive_api.edit_draft_dataset'):
            return obj.created_by == request.user or request.user.groups.filter(name='NGT Administrator').exists()
        elif obj.status == SUBMITTED:
            return request.user.groups.filter(name='NGT Administrator').exists()
        elif obj.status == APPROVED and request.user.groups.filter(name='NGT Administrator').exists():
            raise PermissionDenied(detail='A data set in APPROVED status may not be edited')

        return False


class DataSetViewSet(ModelViewSet):
    """
        Returns a list of all  DataSets available to the archive_api service

    """
    permission_classes = (HasEditPermissionOrReadonly, permissions.IsAuthenticated)
    queryset = DataSet.objects.all()
    serializer_class = DataSetSerializer
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']
    parser_classes = (JSONParser, MultiPartParser, FormParser)

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

    @detail_route(methods=['GET'],
                  permission_classes=(HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasArchivePermission))
    def archive(self, request, pk=None):

        dataset = self.get_object()

        from django.conf import settings
        # We want the current name of the Dataset as the files name
        dataset_name = dataset.name.replace(" ", "_")
        dataset_name = ''.join([i for i in dataset_name if i.isalnum() or i == "_"])
        dataset_name = dataset_name.replace("__", "_")
        dataset_id_version, file_extension = os.path.splitext(dataset.archive.name)

        fullpath = os.path.join(settings.DATASET_ARCHIVE_ROOT, dataset.archive.name)
        if not dataset.archive:
            return Response({'success': False, 'detail': 'Not found'},
                            status=status.HTTP_404_NOT_FOUND)

        response = HttpResponse()
        response['X-Sendfile'] = smart_str(fullpath)
        response['Content-Disposition'] = 'attachment; filename={}_{}_{}{}'.format(
            dataset.data_set_id(), dataset.version, dataset_name, file_extension)
        return response

    @detail_route(methods=['POST'],
                  permission_classes=(HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasUploadPermission))
    def upload(self, request, *args, **kwargs):
        """
        Upload an archive file to the Dataset

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if 'attachment' in request.data:
            dataset = self.get_object()
            upload = request.data['attachment']

            try:
                # This will rollback the transaction on failure
                with transaction.atomic():
                    # Validate the archive field with clean()
                    dataset.archive.field.clean(upload, dataset)
                    dataset.archive.save(upload.name, upload)
            except ValidationError as ve:
                return Response({'success': False, 'detail': ve.detail},
                                status=status.HTTP_400_BAD_REQUEST)

            return Response({'success': True, 'detail': 'File uploaded'},
                            status=status.HTTP_201_CREATED, headers={'Location':
                                                                         dataset.archive.url})
        else:
            return Response({'success': False, 'detail': 'There is no file to upload'},
                            status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post', 'get'],
                  permission_classes=(HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasApprovePermission))
    def approve(self, request, pk=None):
        """
        Approve action.  Changes the dataset from 'submitted' to approved status. User must have the
        proper permissions for this action

        :param request:
        :param pk:
        :return:
        """

        self.change_status(request, APPROVED)
        return Response({'success': True, 'detail': 'DataSet has been approved.'}, status=status.HTTP_200_OK)

    @detail_route(methods=['post', 'get'],
                  permission_classes=(HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasUnsubmitPermission))
    def unsubmit(self, request, pk=None):
        """
        Unsubmit action.  Changes the dataset from 'submitted' to draft status. User must have the
        proper permissions for this action

        :param request:
        :param pk:
        :return:
        """

        self.change_status(request, DRAFT)
        return Response({'success': True, 'detail': 'DataSet has been unsubmitted.'}, status=status.HTTP_200_OK)

    @detail_route(methods=['post', 'get'],
                  permission_classes=(
                  HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasUnapprovePermission))
    def unapprove(self, request, pk=None):
        """
        Unapprove action.  Changes the dataset from 'approved' to submitted status. User must have the
        proper permissions for this action

        :param request:
        :param pk:
        :return:
        """

        self.change_status(request, SUBMITTED)
        return Response({'success': True, 'detail': 'DataSet has been unapproved.'}, status=status.HTTP_200_OK)

    @detail_route(methods=['post', 'get'],
                  permission_classes=(HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasSubmitPermission))
    def submit(self, request, pk=None):
        """
        Submit action. Changes the dataset from 'draft' to 'submitted' status. User must have
        the proper permissions for this action.

        :param request:
        :param pk:
        :return:
        """
        self.change_status(request, SUBMITTED)
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
        Returns a list of all  Sites available to the archive_api service
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
