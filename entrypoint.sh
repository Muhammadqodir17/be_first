#!/bin/bash

set -e
set -o errexit
set -o nounset

echo "Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."

while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
    echo "Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."
    sleep 2
done

python manage.py makemigrations
python ./manage.py migrate
python ./manage.py collectstatic --no-input

exec "$@"