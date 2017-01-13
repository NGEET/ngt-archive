from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

import archive_api

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
            return True  # Admin always has access
        elif obj.access_level == PRIVATE:
            return obj.created_by == request.user  # owner always has access
        elif obj.access_level == NGEET:
            return request.user.groups.filter(name__in=['NGT Team','NGT Collaborator']).exists()  # All NGT User has access
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
