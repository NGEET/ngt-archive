#!/usr/bin/env python

import sys

from setuptools import setup
if sys.version_info < (2,6):
    sys.exit('Sorry, Python < 2.6 is not supported')
elif sys.version_info < (2,7):
    sys.exit('Sorry, Python < 2.7 is not supported')

setup(name='ngt_archive',
      version='1.0',
      description='NGEE Tropics Archive Service',
      author='Val Hendrix',
      author_email='vchendrix@lbl.gov',
      packages = ['ngt_archive'],
      py_modules = ['manage'],
      install_requires=[
            "django >= 1.8",
            "djangorestframework == 3.4.3",
            "django-filter ==  0.13.0",
            "pyldap",
            "django-auth-ldap == 1.2.8",
            "djangorestframework-camel-case"
      ]
     )
