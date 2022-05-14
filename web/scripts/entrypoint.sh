#!/bin/bash

set -e

python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput

echo "STARTING GUNICORN SERVER..."
gunicorn config.wsgi:application -t 1800 --bind :8000