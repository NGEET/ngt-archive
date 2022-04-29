#!/usr/bin/env python
import os
import subprocess
import sys

from setuptools import find_packages, setup

# Update version from latest git tags.
# Create a version file in the root directory
version_py = os.path.join(os.path.dirname(__file__), 'ngt_archive/version.py')
try:
    git_describe = subprocess.check_output(["git", "describe", "--tags"]).rstrip().decode('utf-8')
    version_msg = "# Managed by setup.py via git tags.  **** DO NOT EDIT ****"
    with open(version_py, 'w') as f:
        f.write(version_msg + os.linesep + "__version__='" + git_describe.split("-")[0] + "'")
        f.write(os.linesep + "__release__='" + git_describe + "'" + os.linesep)

except Exception as e:
    # If there is an exception, this means that git is not available
    # We will used the existing version.py file
    pass

try:
    with open(version_py) as f:
        code = compile(f.read(), version_py, 'exec')
        exec(code)
except:
    __release__ = None

packages = find_packages(exclude=["*.tests", ])

if sys.version_info < (3, 6):
    sys.exit('Sorry, Python < 3.6 is not supported')

setup(name='ngt_archive',
      url="https://github.com/NGEET/ngt-archive",
      version=__release__,
      description='NGEE Tropics Archive Service',
      author='Val Hendrix',
      author_email='vchendrix@lbl.gov',
      packages=packages,
      py_modules=['manage'],
      include_package_data=True,
      install_requires=[
          "Django == 3.1.14",
          "djangorestframework >= 3.11.0",
          "django-filter >= 2.2.0",
          "django-daterangefilter >= 1.0.0",
          "pyldap>=3.0.0",
          "django-auth-ldap>=2.1.1",
          "django-oauth-toolkit",
          "pytz",
          "django-simple-history",
          "cryptography",
          "celery",
          "django_celery_results",
          "requests",
          "requests_toolbelt"
      ]
      )
