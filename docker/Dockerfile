ARG PYTHON_VERSION=3.9
FROM python:${PYTHON_VERSION}
MAINTAINER Valerie Hendrix <vchendrix@lbl.gov>

# Docker Image Arguments
#  These may be overriden when
#  The image is build
ARG UID=4999
ARG GID=5000

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# The working directory where the
# Application is copied
WORKDIR /app

# Run OS updates
# create unprivileged user, create application directories, and ensure proper permissions
# Install application dependencies
RUN apt-get update &&  apt-get install -y --no-install-recommends libldap2-dev libsasl2-dev libssl-dev netcat-traditional\
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g ${GID} webapp \
    && useradd -u ${UID} -g ${GID} -c 'Web app User' webapp \
    && mkdir -p /app/static \
    && chown -R webapp:webapp /app \
    && chmod -R g+ws  /app

# Copy the application source code
ADD archive_api/ /app/archive_api
ADD ngt_archive/ /app/ngt_archive
ADD licenses/ /app/licenses
ADD docs/ /app/docs
ADD ui/ /app/ui
COPY docker/local.py /app/ngt_archive
COPY pyproject.toml /app/
COPY manage.py /app
COPY README.md /app


#Install the application dependencies
RUN pip install --upgrade pip && \
    pip install "/app[deploy]" && \
    ls -ld /app/static && \
    python -c 'import ngt_archive.settings'


COPY ./docker/docker-entrypoint.sh /usr/local/bin/
RUN ln -s usr/local/bin/docker-entrypoint.sh / # backwards compat

# This can be used for executing manage.py commands in a crom
COPY ./docker/docker-manage-entrypoint.sh /usr/local/bin/
RUN ln -s usr/local/bin/docker-manage-entrypoint.sh / # backwards compat

ENTRYPOINT ["docker-entrypoint.sh"]

USER webapp

