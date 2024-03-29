from __future__ import print_function

from base64 import b64encode
from django.conf.locale.en import formats as en_formats

"""
Django settings for ngt_archive project.

Generated by 'django-admin startproject' using Django 1.9.8.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import sys

import os

# HOSTNAME for use in DOI site urls
SERVICE_HOSTNAME = os.getenv("SERVICE_HOSTNAME", "ngt-data.lbl.gov")
READ_ONLY = os.getenv("READ_ONLY", "false").lower() == "true"

LOGIN_URL = "/api/api-auth/login/"
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 's%=!5j-^-&07^h@$kj_axc0k#87@)ept_k@(qj0l*y(1npx(!u'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'ngt_archive',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ui.apps.UiConfig',
    'rest_framework',
    'archive_api.apps.ArchiveApiConfig',
    'oauth2_provider',
    "simple_history",
    "django_celery_results"
]

MIDDLEWARE= [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'ngt_archive.middleware.TimezoneMiddleware'

]

ROOT_URLCONF = 'ngt_archive.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 'DIRS': [os.path.join(BASE_DIR, 'templates')]
        # ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'ngt_archive': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'archive_api': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        }
    },
}

WSGI_APPLICATION = 'ngt_archive.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = (
    'archive_api.backends.ModelBackend',
)
# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

en_formats.DATETIME_FORMAT = "m/d/Y H:i e"

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    'SCOPES': {'read': 'Read scope', 'write': 'Write scope'},
    'DEFAULT_SCOPES': ['read', 'write']
}


REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.DjangoModelPermissions',
        'archive_api.permissions.IsActivated',

    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_VERSION': 'v1',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',  # Any other renders
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),

}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_ROOT = "static/"
STATIC_URL = '/static/'

ARCHIVE_API = {
    'DATASET_ARCHIVE_ROOT': os.path.join(os.getenv('DATASET_ARCHIVE_ROOT', BASE_DIR), "archives/"),
    # X-Sendfile (apache), X-Accel-Redirect (nginx)
    'DATASET_ARCHIVE_SENDFILE_METHOD': os.getenv('DATASET_ARCHIVE_SENDFILE_METHOD', None),
    'DATASET_ARCHIVE_URL': '/data',  # not used
    'DATASET_ADMIN_MAX_UPLOAD_SIZE': 2147483648, # in bytes
    'DATASET_USER_MAX_UPLOAD_SIZE': 1073741824, # in bytes
    'EMAIL_NGEET_TEAM': 'NGEE Tropics Archive Test <ngeet-team@testserver>',
    'EMAIL_SUBJECT_PREFIX': '[ngt-archive-test]',
    # SECURITY WARNING: keep the secret key used in production secret!
    # Use cryptography library to create a Fernet key (pip install cryptography)
    # >>> from cryptography.fernet import Fernet
    # >>> Fernet.generate_key()
    'SERVICE_ACCOUNT_SECRET_KEY': os.getenv('SERVICE_ACCOUNT_SECRET_KEY', 'JTYRKA98wMg_VQDotXR4ApXfZgH6HBWLHvWwPGtogjw=')
}

# tmp directory at the archive root directory
FILE_UPLOAD_TEMP_DIR = os.path.join(ARCHIVE_API['DATASET_ARCHIVE_ROOT'], "tmp")

GOOGLE_MAPS_KEY = "a secret key"

try:
    try:
        from ngt_archive.local import *
        print("DJANGO loading ngt_archive.local FOUND\n", file=sys.stdout)
    except ImportError:
        from settings.local import *
        print("DJANGO loading settings.local FOUND\n", file=sys.stdout)
except ImportError:
    import logging
    logging.info("DJANGO local settings NOT found. Using default settings")

AUTH_LDAP_SERVER_URI = os.getenv('AUTH_LDAP_SERVER_URI', None)
if AUTH_LDAP_SERVER_URI:
    #####################
    # LDAP configuration
    #####################
    import ldap

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

# Celery Configuration Options
CELERY_TIMEZONE = TIME_ZONE
CELERY_TRACK_STARTED: True
CELERY_RESULT_BACKEND = 'django-db'
# Enables extended task result attributes (name, args, kwargs,
# worker, retries, queue, delivery_info) to be written to backend.
CELERY_RESULT_EXTENDED = True

# CELERY_TASK_TIME_LIMIT = 30 * 60
# CELERY_TASK_ALWAYS_EAGER is set, tasks called using  apply_async or delay  are called directly,
#     without requiring any broker or celery worker. Change this for production
CELERY_TASK_ALWAYS_EAGER = False
CELERY_EAGER_PROPAGATES = False
