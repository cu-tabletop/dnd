#!/bin/bash

poetry run python manage.py migrate --noinput
exec poetry run gunicorn --workers=4 --bind=0.0.0.0:8000 --access-logfile - --error-logfile - my_app.wsgi:application
