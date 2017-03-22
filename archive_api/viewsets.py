# Create your views here.
import inspect
import shutil
from collections import OrderedDict

import os
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.utils.encoding import smart_str
from rest_framework import permissions
from rest_framework import status as http_status
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ValidationError
from rest_framework.metadata import SimpleMetadata
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from types import FunctionType

from archive_api.models import DataSet, MeasurementVariable, Site, Person, Plot, DataSetDownloadLog
from archive_api.permissions import HasArchivePermission, HasSubmitPermission, HasApprovePermission, \
    HasUnsubmitPermission, \
    HasUnapprovePermission, HasUploadPermission, HasEditPermissionOrReadonly, APPROVED, DRAFT, \
    SUBMITTED, IsActivated
from archive_api.serializers import DataSetSerializer, MeasurementVariableSerializer, \
    SiteSerializer, PersonSerializer, \
    PlotSerializer
from archive_api.signals import dataset_status_change


def get_ip_address(request):
    """
    Get IP address from the specified request. This should handle
    proxy requests.
    :param request:
    :return:
    """
    headers = ('HTTP_X_REAL_IP', 'HTTP_CLIENT_IP', 'HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR')
    for header in headers:
        ip = request.META.get(header)
        if ip:
            return ip.split(",")[0].strip()


class DataSetMetadata(SimpleMetadata):
    def determine_metadata(self, request, view):
        """ Customize metadata from OPTIONS method to add detail_route information"""

        data = super(DataSetMetadata, self).determine_metadata(request, view)

        for x, y in view.__class__.__dict__.items():
            if type(y) == FunctionType and hasattr(y, "detail"):
                data.setdefault("detail_routes", default=OrderedDict())
                data["detail_routes"].setdefault(x, default=OrderedDict())
                detail_route = data["detail_routes"][x]
                detail_route["allowed_methods"] = y.bind_to_methods
                detail_route["description"] = inspect.getdoc(y)  # get clean text

        upload_route = data["detail_routes"]["upload"]
        upload_route["parameters"] = {"attachment": {
            "type": "file",
            "required": True
        }}

        return data


class DataSetViewSet(ModelViewSet):
    """
        Returns a list of all  DataSets available to the archive_api service
    """
    permission_classes = (HasEditPermissionOrReadonly, permissions.IsAuthenticated, IsActivated,
                          permissions.DjangoModelPermissions)
    queryset = DataSet.objects.all()
    serializer_class = DataSetSerializer
    http_method_names = ['get', 'post', 'put', 'head', 'options']
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    metadata_class = DataSetMetadata

    def perform_create(self, serializer):
        """
        Override the update method to update the created_by and modified by fields.]
        """
        if self.request.user.is_authenticated and serializer.is_valid():
            instance = serializer.save(created_by=self.request.user, modified_by=self.request.user)

            # Send signal for the status change
            dataset_status_change.send(sender=self.__class__, request=self.request,
                                       user=self.request.user,
                                       instance=instance, original_status=None)

    def perform_update(self, serializer):
        """
        Override the update method to update the modified by fields.
        """
        if self.request.user.is_authenticated and serializer.is_valid():
            serializer.save(modified_by=self.request.user)

    @detail_route(methods=['GET'],
                  permission_classes=(
                  HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasArchivePermission))
    def archive(self, request, pk=None):

        dataset = self.get_object()

        from django.conf import settings
        head, tail = os.path.split(dataset.archive.name)

        fullpath = os.path.join(settings.ARCHIVE_API['DATASET_ARCHIVE_ROOT'], dataset.archive.name)
        if not dataset.archive:
            return Response({'success': False, 'detail': 'Not found'},
                            status=http_status.HTTP_404_NOT_FOUND)

        response = HttpResponse()
        response['X-Sendfile'] = smart_str(fullpath)
        response['Content-Disposition'] = 'attachment; filename={}'.format(tail)

        DataSetDownloadLog.objects.create(
            user=request.user,
            dataset=dataset,
            dataset_status=dataset.status,
            request_url=request.path[:255],
            ip_address=get_ip_address(request)
        )

        return response

    @detail_route(methods=['post'],
                  permission_classes=(
                  HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasUploadPermission))
    def upload(self, request, *args, **kwargs):
        """
        Upload an archive file to the Dataset
        """
        if 'attachment' in request.data:
            dataset = self.get_object()

            upload = request.data['attachment']

            if request.user.has_perm("archive_api.upload_large_file_dataset") and upload.size > \
                    settings.ARCHIVE_API['DATASET_ADMIN_MAX_UPLOAD_SIZE']:
                return Response({'success': False,
                                 'detail': 'Uploaded file size is {:.1f} MB. Max upload size is {:.1f} MB'.format(
                                     upload.size / (1024 * 1024),
                                     settings.ARCHIVE_API['DATASET_ADMIN_MAX_UPLOAD_SIZE'] / (
                                     1024 * 1024)
                                 )}, status=http_status.HTTP_400_BAD_REQUEST)
            elif upload.size > settings.ARCHIVE_API['DATASET_USER_MAX_UPLOAD_SIZE']:
                return Response({'success': False,
                                 'detail': 'Uploaded file size is {:.1f} MB. Max upload size is {:.1f} MB'.format(
                                     upload.size / (1024 * 1024),
                                     settings.ARCHIVE_API['DATASET_USER_MAX_UPLOAD_SIZE'] / (
                                     1024 * 1024)
                                 )}, status=http_status.HTTP_400_BAD_REQUEST)

            try:
                # This will rollback the transaction on failure
                with transaction.atomic():
                    # Validate the archive field with clean()
                    dataset.archive.field.clean(upload, dataset)
                    dataset.archive.save(upload.name, upload)
                    dataset.modified_by = request.user
                    dataset.save()
            except ValidationError as ve:
                return Response({'success': False, 'detail': ve.detail},
                                status=http_status.HTTP_400_BAD_REQUEST)
            finally:
                upload.close()

            return Response({'success': True, 'detail': 'File uploaded'},
                            status=http_status.HTTP_201_CREATED, headers={'Location':
                                                                              dataset.archive.url})
        else:
            return Response({'success': False, 'detail': 'There is no file to upload'},
                            status=http_status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post', 'get'],
                  permission_classes=(
                  HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasApprovePermission))
    def approve(self, request, pk=None):
        """
        Approve action.  Changes the dataset from SUBMITTED to APPROVED status. User must permissions for this action
        """

        self.change_status(request, APPROVED)
        return Response({'success': True, 'detail': 'DataSet has been approved.'},
                        status=http_status.HTTP_200_OK)

    @detail_route(methods=['post', 'get'],
                  permission_classes=(
                  HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasUnsubmitPermission))
    def unsubmit(self, request, pk=None):
        """
        Unsubmit action.  Changes the dataset from SUBMITTED to DRAFT status. User must have permissions for this action
        """

        self.change_status(request, DRAFT)
        return Response({'success': True, 'detail': 'DataSet has been unsubmitted.'},
                        status=http_status.HTTP_200_OK)

    @detail_route(methods=['post', 'get'],
                  permission_classes=(
                          HasEditPermissionOrReadonly, permissions.IsAuthenticated,
                          HasUnapprovePermission))
    def unapprove(self, request, pk=None):
        """
        Unapprove action.  Changes the dataset from APPROVED to SUBMITTED status. User must have permissions for this action
        """

        self.change_status(request, SUBMITTED)
        return Response({'success': True, 'detail': 'DataSet has been unapproved.'},
                        status=http_status.HTTP_200_OK)

    @detail_route(methods=['post', 'get'],
                  permission_classes=(
                  HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasSubmitPermission))
    def submit(self, request, pk=None):
        """
        Submit action. Changes the dataset from DRAFT to SUBMITTED status. User must have permissions for this action.
        """
        self.change_status(request, SUBMITTED)
        return Response({'success': True, 'detail': 'DataSet has been submitted.'},
                        status=http_status.HTTP_200_OK)

    def change_status(self, request, status):
        """
        Change the status of the dataset. This will raise and exception on ValidationErrors and
        invalid permissions.
        """
        dataset = self.get_object()  # this will initiate a permissions check
        original_status = dataset.status
        dataset.status = status

        # This will rollback the transaction on failure
        with transaction.atomic():
            # Validate the archive field with clean()
            dataset.submission_date = timezone.now()
            dataset.modified_by = request.user
            serializer = DataSetSerializer(dataset, context={'request': request})
            deserializer = DataSetSerializer(dataset, data=serializer.data,
                                             context={'request': request})
            deserializer.is_valid(raise_exception=True)
            self.perform_update(deserializer)
            if status == SUBMITTED and dataset.archive and dataset.version == "0.0":

                old_path, filename = os.path.split(dataset.archive.name)
                dataset.version = "1.0"  # FIXME:  hard coded util statemachine is implemented
                new_path = old_path.replace("0.0", dataset.version)
                os.makedirs(os.path.join(settings.ARCHIVE_API['DATASET_ARCHIVE_ROOT'], new_path),
                            exist_ok=True)
                shutil.copy2(
                    os.path.join(settings.ARCHIVE_API['DATASET_ARCHIVE_ROOT'], old_path, filename),
                    os.path.join(settings.ARCHIVE_API['DATASET_ARCHIVE_ROOT'], new_path, filename))

                dataset.archive.name = "{}/{}".format(new_path, filename)
                dataset.save()

        # Send the signal for the status change
        dataset_status_change.send(sender=self.__class__, request=request, user=request.user,
                                   instance=dataset, original_status=original_status)

    def get_queryset(self):
        """
        This view should return a list of all the datasets
        for the currently authenticated user.

        NGT Administrators are allow to view all datasets
        NGT Team and Collaborators are allow to view public, their own private and approved NGEET datasets
        """
        user = self.request.user

        from django.db.models import Q  # for or clause
        if self.request.user.has_perm('archive_api.view_all_datasets'):
            return DataSet.objects.filter(status__gte=DataSet.STATUS_DRAFT)
        else:
            where_clause = Q(created_by=user, status__gte=DataSet.STATUS_DRAFT) | Q(
                access_level=DataSet.ACCESS_PUBLIC, status=DataSet.STATUS_APPROVED) | Q(
                Q(cdiac_submission_contact__user=user,
                  status__gte=DataSet.STATUS_DRAFT,
                  cdiac_import=True)
            )

            if self.request.user.has_perm('archive_api.view_ngeet_approved_datasets'):
                where_clause = where_clause | Q(access_level=DataSet.ACCESS_NGEET,
                                                status=DataSet.STATUS_APPROVED)
            return DataSet.objects.filter(where_clause)


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
