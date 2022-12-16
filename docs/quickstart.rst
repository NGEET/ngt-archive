==========
Quickstart
==========
NGEE Tropics Archive is a  Django app that acts as a data archive for the NGEE Tropics project.
Use these instructions as a starting point for deploying the application. Please refer to Django
documentation at https://docs.djangoproject.com for deployment configuration options.

Get the Source code
-------------------
First the source code needs to be checked out::

    git clone git@github.com:NGEET/ngt-archive.git
    cd ngt-archive

Checkout the Tagged Version
---------------------------
Get the desired version::

    git checkout <version_number>


Setup the App
-------------
::

    (ngt-archive)$ pip install ".[deploy]"

Prepare Settings
----------------
Now you need to prepare your application settings::

    $ touch ngeet_archive_settings.py

General Settings
~~~~~~~~~~~~~~~~
Add the following to ``ngeet_archive_settings.py`` replacing the items in curly braces with your values.
These are the main settings that will change depending on deployment environment
(e.g. production, development, test)::

    from ngt_archive.settings import *

    DEBUG = True # Change to False for production deployments

    # Uncomment for Production (Add allowable hostnames)
    #ALLOWED_HOSTS = []

    # don't want emails while developing
    # Production - added admins to email for errors
    ADMINS = ()
    MANAGERS = ADMINS

    # Refer to the Django documentation for a list of
    # available email backends
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    SECRET_KEY = {{ random string for secret key }}

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/1.6/howto/static-files/

    STATIC_URL = '/static/'
    STATICFILES_DIRS = (

    )
    # Where the static files are physcially located
    #STATIC_ROOT =

Archive API Settings
~~~~~~~~~~~~~~~~~~~~
Below are the archive api settings.  Customize these for different deployments (e.g production,
development, test)::

    ARCHIVE_API = {
        'DATASET_ARCHIVE_ROOT': os.path.join(BASE_DIR, "archives/"),
        'DATASET_ARCHIVE_URL': '/archives/',  # not used
        'DATASET_ADMIN_MAX_UPLOAD_SIZE': 2147483648, # in bytes
        'DATASET_USER_MAX_UPLOAD_SIZE': 1073741824, # in bytes
        'EMAIL_NGEET_TEAM': ['ngeet-team@testserver'],
        'EMAIL_SUBJECT_PREFIX' : '[ngt-archive-test]'

    }

Database Settings
~~~~~~~~~~~~~~~~~
Add the following to Postgres DB connection details to ``ngeet_archive_settings.py``. Replace the
items in curly braces with your values.::

    DATABASES = {

    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'geo',
        'USER': '{{ db_user }} ',
        'PASSWORD': '{{ db_password }}',
        'HOST': 'localhost',
        'PORT': '',
        }
    }



Migrate the App
---------------

Run ``python manage.py migrate`` to create the JAEA Geo models. This will create the materialized views and load the app's
plugins::

    (ngt-archive)$ DJANGO_SETTINGS_MODULE=ngeet_archive_settings ./manage.py migrate

Static Files
------------
Run ``python manage.py collectstatic`` to deploy the static files to the production server.  Note that the pages will be deployed
to STATIC_ROOT. If no value is supplied the static directory will be created in the current directory.::

    (ngt-archive)$ DJANGO_SETTINGS_MODULE=ngt-archive_settings ./manage.py collectstatic

Create a Superuser
------------------
In order to access your development website, you need to create a superuser::

    (ngt-archive)$ DJANGO_SETTINGS_MODULE=ngeet_archive_settings ./manage.py createsuperuser

Now you may start your development server and login.

Run the Server
--------------
Start the development server and visit http://127.0.0.1:8000/admin/
to manage a JAEA Geo  users ::

    (ngt-archive)$ ./manage.py runserver

Visit http://127.0.0.1:8000/api/v1 to to view the REST api.

For deployment options see the Django documentation at https://docs.djangoproject.com




