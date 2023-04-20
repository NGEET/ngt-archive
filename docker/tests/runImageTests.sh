#!/usr/bin/env bash
set -eo pipefail


# Success check mark for test
function success {
  printf "\xE2\x9C\x94 %s\n" "$1"
}

# Fail red x for test
function fail {
  printf "\xE2\x9D\x8C %s\n" "$1"
}

# Function to Clean up testing artifacts
function finish {
  echo "******************************"
  echo "Cleaning up testing artifacts"
  echo "******************************"
  docker stop $cid
  docker rm -vf $cid
}

# Remove container afterwards
trap finish EXIT

[ "$DEBUG" ] && set -x

# Set current working directory
cd "$(dirname "$0")"

dockerImage=$1

if ! docker inspect "$dockerImage" &> /dev/null; then
    echo $'\timage does not exist!'
    exit
fi

echo "Starting up container "
# Create an instance of the container-under-test
cid=$(docker run  -d \
      -it $dockerImage \
      uwsgi --module ngt_archive.wsgi:application --http-socket 0.0.0.0:8080 --static-map /static=/app/static )
echo "Started up container $cid"

echo "Start Tests"
#Run Tests

pwd=/app
TEST_PWD="$(docker exec "$cid" pwd )"
[ "$TEST_PWD" == "$pwd" ] || (fail "Incorrect pwd $TEST_PWD it should be $pwd" && exit 1)
success "Working directory is correct"

# Check for manage.py
[ $(docker exec $cid ls manage.py | grep 'manage.py' | wc -l) -ne 0 ] || (fail "manage.py missing" && exit 1)
success "Found manage.py"

# Is the  Application directory there
[ $(docker exec $cid python -c 'import ngt_archive; print(ngt_archive.__file__)' | grep 'ngt_archive' | wc -l) -ne 0  ] || \
    (fail "missing\n" && exit 1)
success "NGT Archive is installed"

# Give time to start up
sleep 5

# is the app running
[ $(docker exec $cid ps auxwww | grep 'ngt_archive.wsgi:application' | wc -l) -gt 1 ] || (fail "NGT Archive is not running" && exit 1)
success "NGT Archive is running"

echo "**********"
echo "SUCCESS!!"
echo "**********"