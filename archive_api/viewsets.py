# Create your views here.
import inspect
import mimetypes
import shutil
from collections import OrderedDict

import os
from wsgiref.util import FileWrapper

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.utils import timezone
from django.utils.encoding import smart_str
from rest_framework import permissions
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.metadata import SimpleMetadata
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from types import FunctionType

from archive_api.models import DataSet, MeasurementVariable, STATUS_CHOICES, Site, Person, Plot, DataSetDownloadLog
from archive_api.permissions import HasArchivePermission, HasSubmitPermission, HasApprovePermission, \
    HasUploadPermission, HasEditPermissionOrReadonly, APPROVED, DRAFT, \
    SUBMITTED, IsActivated
from archive_api.serializers import DataSetSerializer, MeasurementVariableSerializer, \
    SiteSerializer, PersonSerializer, \
    PlotSerializer
from archive_api.signals import dataset_status_change, dataset_doi_issue
from archive_api.service import osti

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


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
        """ Customize metadata from OPTIONS method to add action information"""

        data = super(DataSetMetadata, self).determine_metadata(request, view)

        max_file_length = request.user.has_perm("archive_api.upload_large_file_dataset") and \
                          settings.ARCHIVE_API['DATASET_ADMIN_MAX_UPLOAD_SIZE'] or \
                          settings.ARCHIVE_API['DATASET_USER_MAX_UPLOAD_SIZE']

        for x, y in view.__class__.__dict__.items():
            if type(y) == FunctionType and hasattr(y, "detail"):
                data.setdefault("actions", OrderedDict())
                data["actions"].setdefault(x, OrderedDict())
                action = data["actions"][x]
                action["allowed_methods"] = y.mapping.keys()
                action["description"] = inspect.getdoc(y)  # get clean text

        upload_route = data["actions"]["upload"]
        upload_route["parameters"] = {"attachment": {
            "type": "file",
            "required": True,
            "max_length": max_file_length
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
        Override the update method to update the managed_by and modified by fields.]
        """
        if self.request.user.is_authenticated and serializer.is_valid():
            instance = serializer.save(managed_by=self.request.user, modified_by=self.request.user)

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

    @action(detail=True, methods=['GET'],
            permission_classes=(
                    HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasArchivePermission))
    def archive(self, request, pk=None):

        dataset = self.get_object()

        from django.conf import settings
        head, tail = os.path.split(dataset.archive.name)

        if not dataset.archive:
            return Response({'success': False, 'detail': 'Not found'},
                            status=http_status.HTTP_404_NOT_FOUND)

        file_path = os.path.join(settings.ARCHIVE_API['DATASET_ARCHIVE_ROOT'], dataset.archive.name)
        file_mimetype = mimetypes.guess_type(file_path)

        sendfile_method = os.getenv('DATASET_ARCHIVE_SENDFILE_METHOD', None)
        if not sendfile_method:
            # This should only be the development method
            file_wrapper = FileWrapper(open(file_path, 'rb'))
            response = HttpResponse(file_wrapper, content_type=file_mimetype)
        else:
            # This should either be a setup for apache or nginx
            response = HttpResponse(content_type=file_mimetype)
            response[sendfile_method] = smart_str(file_path)
            logger.info(f"{sendfile_method}:{response[sendfile_method]}")

        response['Content-Length'] = os.stat(file_path).st_size
        response['Content-Disposition'] = 'attachment; filename={}'.format(tail)

        logger.info(
            f"Content-Length:{response['Content-Length']} Content-Disposition:{response['Content-Disposition']}")

        DataSetDownloadLog.objects.create(
            user=request.user,
            dataset=dataset,
            dataset_status=dataset.status,
            request_url=request.path[:255],
            ip_address=get_ip_address(request)
        )

        return response

    @action(detail=True, methods=['post'],
            permission_classes=(
                    HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasUploadPermission))
    def upload(self, request, *args, **kwargs):
        """
        Upload an archive file to the Dataset
        """
        if 'attachment' in request.data:
            dataset = self.get_object()

            upload = request.data['attachment']

            # Get the max upload size depending on the user's permissions
            maxUploadSize = request.user.has_perm("archive_api.upload_large_file_dataset") and \
                            settings.ARCHIVE_API['DATASET_ADMIN_MAX_UPLOAD_SIZE'] or \
                            settings.ARCHIVE_API['DATASET_USER_MAX_UPLOAD_SIZE']

            if upload.size > maxUploadSize:
                return Response({'success': False,
                                 'detail': 'Uploaded file size is {:.1f} MB. Max upload size is {:.1f} MB'.format(
                                     upload.size / (1024 * 1024),
                                     maxUploadSize / (
                                             1024 * 1024)
                                 )}, status=http_status.HTTP_400_BAD_REQUEST)

            try:
                # This will rollback the transaction on failure
                with transaction.atomic():
                    # Validate the archive field with clean()
                    dataset.archive.field.clean(upload, dataset)
                    dataset._change_reason = f'{request.path}: Saved upload file "{upload.name}"'
                    dataset.archive.save(upload.name, upload)
                    dataset.modified_by = request.user
                    if dataset.managed_by == request.user:
                        dataset.status = dataset.STATUS_DRAFT
                    dataset._change_reason = f'{request.path}: Saved dataset with file path "{dataset.archive}"'
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

    @action(detail=True, methods=['post', 'get'],
            permission_classes=(
                    HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasApprovePermission))
    def approve(self, request, pk=None):
        """
        Approve action.  Changes the dataset from SUBMITTED to APPROVED status. User must permissions for this action
        """

        self.change_status(request, APPROVED)
        return Response({'success': True, 'detail': 'DataSet has been approved.'},
                        status=http_status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'get'],
            permission_classes=(
                    HasEditPermissionOrReadonly, permissions.IsAuthenticated, HasSubmitPermission))
    def submit(self, request, pk=None):
        """
        Submit action. Changes the dataset from DRAFT to SUBMITTED status. User must have permissions for this action.
        """
        self.change_status(request, SUBMITTED)
        return Response({'success': True, 'detail': 'DataSet has been submitted.'},
                        status=http_status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'get'],
            permission_classes=(
                    HasEditPermissionOrReadonly, permissions.IsAuthenticated))
    def draft(self, request, pk=None):
        """
        Submit action. Changes the dataset from DRAFT to SUBMITTED status. User must have permissions for this action.
        """
        self.change_status(request, DRAFT)
        return Response({'success': True, 'detail': 'DataSet has been update.'},
                        status=http_status.HTTP_200_OK)

    def change_status(self, request, status):
        """
        Change the status of the dataset. This will raise and exception on ValidationErrors and
        invalid permissions.
        """
        dataset = self.get_object()  # this will initiate a permissions check
        original_status = dataset.status
        now = timezone.now()
        doi_function = None

        if original_status != status:

            # This will rollback the transaction on failure
            with transaction.atomic():
                # Validate the archive field with clean()
                dataset.modified_by = request.user
                dataset.status = status
                serializer = DataSetSerializer(dataset, context={'request': request})
                deserializer = DataSetSerializer(dataset, data=serializer.data,
                                                 context={'request': request})
                deserializer.is_valid(raise_exception=True)

                # The status has changed
                if status == SUBMITTED:
                    doi_function = osti.mint

                    # This is the first time that dataset is being submitted
                    dataset.submission_date = now
                    if dataset.archive and dataset.version == "0.0":
                        dataset.version = "1.0"

                elif status == APPROVED:
                    doi_function = osti.publish
                    dataset.approval_date = now
                    if original_status == SUBMITTED and not dataset.publication_date:
                        # The dataset is NOT LIVE yet and is being approved for the first time
                        dataset.publication_date = now
                        dataset.status = status

                dataset._change_reason = f'{request.path}: Changed Status from {STATUS_CHOICES[original_status]} to ' \
                                         f'{STATUS_CHOICES[status]}'
                dataset.save(modified_date=now)
                dataset.refresh_from_db()

            if doi_function:
                try:
                    # process the DOI
                    osti_record = doi_function(dataset.id)
                    if osti_record and osti_record.status != "SUCCESS":
                        error_message = f"doi:{osti_record.doi} doi_status:{osti_record.doi_status} " \
                                        f"status:{osti_record.status} status_message:{osti_record.status_message}"
                        dataset_doi_issue.send(sender=self.__class__, request=request, user=request.user,
                                               instance=dataset, error_message=error_message)

                except Exception as e:
                    # Send notification to admin if there are any errors
                    dataset_doi_issue.send(sender=self.__class__, request=request, user=request.user,
                                           instance=dataset, error_message=str(e))

            dataset.refresh_from_db()
            # Send the signal for the status change
            dataset_status_change.send(sender=self.__class__, request=request, user=request.user,
                                       instance=dataset, original_status=original_status)

    def get_queryset(self, ):
        """
        This view should return a list of all the datasets
        for the currently authenticated user.

        NGT Administrators are allow to view all datasets
        NGT Team and Collaborators are allow to view public, their own private and approved NGEET datasets
        """
        user = self.request.user
        managed_by = self.request.query_params.get('managed_by', None)
        needs_approval = self.request.query_params.get('needs_approval', None)
        is_published = self.request.query_params.get('is_published', None)

        from django.db.models import Q  # for or clause

        # Filter by datasets the current user has permissions for
        if self.request.user.has_perm('archive_api.view_all_datasets'):
            # This user can view all datasets
            where_clause = Q(status__gte=DataSet.STATUS_DRAFT)
        else:
            # This user can only view their own and public datasets
            where_clause = Q(managed_by=user, status__gte=DataSet.STATUS_DRAFT) | Q(
                access_level=DataSet.ACCESS_PUBLIC, status=DataSet.STATUS_APPROVED) | Q(
                Q(cdiac_submission_contact__user=user,
                  status__gte=DataSet.STATUS_DRAFT,
                  cdiac_import=True)
            )

            if self.request.user.has_perm('archive_api.view_ngeet_approved_datasets'):
                where_clause = where_clause | Q(access_level=DataSet.ACCESS_NGEET,
                                                status=DataSet.STATUS_APPROVED)

        # Filter by is_published
        if is_published == 'true':
            where_clause = where_clause & Q(publication_date__isnull=False, publication_date__lt=timezone.now())
        elif is_published == 'false':
            where_clause = where_clause & Q(publication_date__isnull=True)

        # Filter by managed_by
        if managed_by:
            where_clause = where_clause & Q(managed_by__username=managed_by)

        # Filter by needs approval
        if needs_approval == 'true':
            where_clause = where_clause & Q(status__gte=DataSet.STATUS_SUBMITTED) & \
                           Q(Q(approval_date__lt=F('modified_date')) | Q(approval_date__gt=F('modified_date')) | \
                             Q(approval_date=None))
        elif needs_approval == 'false':
            where_clause = where_clause & Q(status__lt=DataSet.STATUS_SUBMITTED) | Q(approval_date=F('modified_date'))

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
