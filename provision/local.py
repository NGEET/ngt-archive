import ldap
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARCHIVE_API = {
    'DATASET_ARCHIVE_ROOT': os.getenv('DATASET_ARCHIVE_ROOT', os.path.join(BASE_DIR, 'archives')),
    'DATASET_ARCHIVE_URL': '/archives/',  # not used
    'DATASET_ADMIN_MAX_UPLOAD_SIZE': 2147483648, # in bytes
    'DATASET_USER_MAX_UPLOAD_SIZE': 1073741824, # in bytes
    'EMAIL_NGEET_TEAM': (os.getenv('EMAIL_NGEET_TEAM'),),
    'EMAIL_SUBJECT_PREFIX' : os.getenv('EMAIL_SUBJECT_PREFIX', '[ngt-archive]')

}
GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_KEY')

FILE_UPLOAD_PERMISSIONS = 0o660
FILE_UPLOAD_TEMP_DIR = os.path.join(os.getenv('FILE_UPLOAD_TEMP_DIR', '/tmp'))

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.lbl.gov'
EMAIL_PORT = 25
DEFAULT_FROM_EMAIL = 'NGEE Tropics Archive <no-reply@ngt-dev.lbl.gov>'

# django app running behind a reverse proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


# Uncomment for Production (using a reverse proxy)
DEBUG = False
ALLOWED_HOSTS = ['*']

# A list of all the people who get code error notifications. When DEBUG=False
# and a view raises an exception, Django will email these people with the full
# exception information. Each item in the list should be a tuple of (Full name,
# email address).
ADMINS = (('NGEE Tropics Admin', os.getenv('ADMIN_EMAIL')),)
# A list in the same format as ADMINS that specifies who should get broken link
MANAGERS = ADMINS

SECRET_KEY = os.getenv('SECRET_KEY', None)

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.getenv('SQL_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('SQL_DATABASE', os.path.join(BASE_DIR, 'db.sqlite3')),
        'USER': os.getenv('SQL_USER', 'wfsfa'),
        'PASSWORD': os.getenv('SQL_PASSWORD', 'password'),
        'HOST': os.getenv('SQL_HOST', 'localhost'),
        'PORT': os.getenv('SQL_PORT', '5432'),
    }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
import os
STATIC_ROOT = os.getenv('STATIC_ROOT','static/')
STATIC_URL = '/static/'

STATICFILES_DIRS = (

        )


#####################
# LDAP configuration
#####################

AUTH_LDAP_SERVER_URI = os.getenv('AUTH_LDAP_SERVER_URI')
AUTH_LDAP_CONNECTION_OPTIONS = {
            ldap.OPT_REFERRALS: 0
            }

from django_auth_ldap.config import LDAPSearch


AUTH_LDAP_BIND_DN = os.getenv('AUTH_LDAP_BIND_DN')
AUTH_LDAP_BIND_PASSWORD = os.getenv('AUTH_LDAP_BIND_PASSWORD')
AUTH_LDAP_USER_SEARCH = LDAPSearch(os.getenv('AUTH_LDAP_USER_SEARCH'),
            ldap.SCOPE_SUBTREE,
            "(&(objectClass=user)(sAMAccountName=%(user)s))")

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
    'archive_api.backends.LDAPBackend',
    'archive_api.backends.ModelBackend',
    'archive_api.backends.OAuth2Backend',
                )

