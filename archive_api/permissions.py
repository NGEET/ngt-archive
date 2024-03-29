from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

import archive_api


DRAFT = archive_api.models.STATUS_CHOICES[0][0]
SUBMITTED = archive_api.models.STATUS_CHOICES[1][0]
APPROVED = archive_api.models.STATUS_CHOICES[2][0]

PRIVATE = archive_api.models.ACCESS_CHOICES[0][0]
NGEET = archive_api.models.ACCESS_CHOICES[1][0]
PUBLIC = archive_api.models.ACCESS_CHOICES[2][0]


class IsActivated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):

        # Make sure that this is the NGT User
        return request.user and request.user.is_activated


class HasArchivePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        path_info = request.path_info
        if "/archive" not in path_info:
            return False

        if request.user.has_perm("archive_api.view_all_datasets"):
            return True  # Admin always has access
        elif obj.access_level == PRIVATE:
            return obj.managed_by == request.user  # owner always has access
        elif obj.access_level == NGEET:
            return request.user.has_perm("archive_api.view_ngeet_approved_datasets")
        else:
            # This is public, All have access
            return True


class HasSubmitPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        path_info = request.path_info
        if "/submit" not in path_info:
            return False

        if obj.needs_review or obj.submission_date is None:
            return (obj.managed_by == request.user and request.user.has_perm('archive_api.edit_own_dataset')) \
                    or request.user.has_perm('archive_api.edit_all_dataset')
        else:
            raise PermissionDenied(detail='This dataset does not need a review')


class HasApprovePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        path_info = request.path_info
        if "/approve" not in path_info:
            return False

        if request.user.has_perm('archive_api.approve_submitted_dataset'):
            if not obj.needs_approval:
                raise PermissionDenied("This dataset does not need approval")
            else:
                return request.user.has_perm('archive_api.approve_submitted_dataset')

        return False


class HasUploadPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        path_info = request.path_info
        if "/upload" not in path_info:
            return False

        return (obj.managed_by == request.user  and request.user.has_perm('archive_api.edit_own_dataset')) \
            or request.user.has_perm('archive_api.edit_all_dataset')


class HasApprovalDatePermission(permissions.BasePermission):
    """ Object-level permission to only allow admins and owners to set a publication date"""
    def has_object_permission(self, request, view, obj):
        path_info = request.path_info
        if "/approval_date" not in path_info:
            return False

        has_permission  = (obj.managed_by == request.user and request.user.has_perm('archive_api.edit_own_dataset')) \
                   or request.user.has_perm('archive_api.edit_all_dataset')

        # Only submitted and approved dataset may have the publication date set
        if obj.status in [SUBMITTED, APPROVED]:
            return has_permission
        elif has_permission and obj.status == DRAFT:
            raise PermissionDenied(detail='Only a dataset in SUBMITTED or APPROVED status'
                                          ' may have a publication date set.')

        return False


class HasEditPermissionOrReadonly(permissions.BasePermission):
    """
       Object-level permission to only allow owners of an object  or administrators to edit it.
       Assumes the model instance has an `managed_by` attribute.
    """

    def has_object_permission(self, request, view, obj):

        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Owner is either editing or submitting a draft
        if request.method == "DELETE":
            return False
        return (obj.managed_by == request.user and request.user.has_perm('archive_api.edit_own_dataset') )\
            or request.user.has_perm('archive_api.edit_all_dataset')

