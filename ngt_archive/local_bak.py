import ldap

DEBUG = True

# don't want emails while developing
ADMINS = ()
MANAGERS = ADMINS

SECRET_KEY = 'GGH5656HMLFGAA234'

DATABASES = {

'default': {
'ENGINE': 'django.db.backends.postgresql_psycopg2',
'NAME': 'ngt_archive',
'USER': 'ngt_archive',
'PASSWORD': 'changmetosomethingsecret',
'HOST': 'localhost',
'PORT': '',
}
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
import os
STATIC_ROOT = '/vagrant/static'
STATIC_URL = '/static/'

STATICFILES_DIRS = (

)

#####################
# LDAP configuration
#####################

AUTH_LDAP_SERVER_URI = "ldap://scooby.lbl.gov"
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0
}

from django_auth_ldap.config import LDAPSearch


AUTH_LDAP_BIND_DN = "cn=Megha Sandesh,cn=users,dc=flux,dc=local"
AUTH_LDAP_BIND_PASSWORD = "aniketh#8589"
AUTH_LDAP_USER_SEARCH = LDAPSearch("CN=Users,DC=flux,DC=local",
    ldap.SCOPE_SUBTREE, "(&(objectClass=user)(sAMAccountName=%(user)s))")

AUTH_LDAP_CACHE_GROUPS = True
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 300


AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}

# Keep ModelBackend around for per-user permissions and maybe a local
# superuser.
AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# django app running behind a reverse proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')