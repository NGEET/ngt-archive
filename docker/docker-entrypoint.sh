#!/bin/bash

set -e

# Usage: file_env VAR [DEFAULT]
#     e.g file_env 'MY_PASSWORD' 'password'
file_env() {
    local var="$1"
    local fileVar="${var}_FILE"
    local def="${2:-}"
    if [ "${!var:-}" ] && [ "${!fileVar:-}" ]; then
        echo >&2 "error: both $var and $fileVar are set (but are exclusive)"
        exit 1
    fi
    local val="$def"
    if [ "${!var:-}" ]; then
        val="${!var}"
    elif [ "${!fileVar:-}" ]; then
        val="$(< "${!fileVar}")"
    fi
    export "$var"="$val"
    unset "$fileVar"
}

if [ "$DATABASE" = "postgres" ];
then
    echo "Waiting for postgres..."

    while ! nc -z ${SQL_HOST:-db} ${SQL_PORT:-5432}; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi


# Get the secrets
file_env 'ADMIN_PASSWORD' 'change_me'
file_env 'SECRET_KEY' 'change_me'
file_env 'SQL_PASSWORD' 'change_me'
file_env 'GOOGLE_MAPS_KEY' 'change_me'
file_env 'AUTH_LDAP_BIND_PASSWORD' 'change_me'

DJANGO_USERS_JSON_FILE=${DJANGO_USERS_JSON_FILE:-/run/secrets/django_users_json}

pip freeze

# Collect the static files
python manage.py collectstatic --no-input

# Migrate the database
python manage.py migrate

IS_LOADED=$(./manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.count())" | tail -1 )
echo "IS_LOADED:$IS_LOADED"

if [ "${IS_LOADED}" == "0" ];
then

    # load the data base
    if [ -f $DJANGO_USERS_JSON_FILE ];
    then
        python manage.py loaddata $DJANGO_USERS_JSON_FILE
    else
       # Create a default superuser
       ./manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('${ADMIN_USER:-admin}', '${ADMIN_EMAIL-ngee-tropics-archive@lbl.gov}', '${ADMIN_PASSWORD}')"
    fi


fi

exec $@