from django.contrib.auth import backends
from django_auth_ldap import backend as ldap_backend
from oauth2_provider import backends as oauth2_backends

from archive_api.models import NGTUser


class OAuth2Backend(oauth2_backends.OAuth2Backend):
    '''
    Extending to provide a proxy for ngt user
    '''

    def authenticate(self, request=None, **credentials):

        user = super().authenticate(request, **credentials)
        if user:
            return self.get_user(user.id)
        else:
            return user

    def get_user(self, user_id):
        try:
            return NGTUser.objects.get(pk=user_id)
        except NGTUser.DoesNotExist:
            return None


class ModelBackend(backends.ModelBackend):
    '''
    Extending to provide a proxy for ngt user
    '''

    def get_user(self, user_id):
        try:
            return NGTUser.objects.get(pk=user_id)
        except NGTUser.DoesNotExist:
            return None


class LDAPBackend(ldap_backend.LDAPBackend):

    def get_user(self, user_id):
        try:
            return NGTUser.objects.get(pk=user_id)
        except NGTUser.DoesNotExist:
            return None

    def get_user_model(self):
        return NGTUser
