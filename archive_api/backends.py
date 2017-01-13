from django.contrib.auth import backends
from django_auth_ldap import backend as ldap_backend

from archive_api.models import NGTUser


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