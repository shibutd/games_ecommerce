#!/bin/bash

python manage.py migrate

python manage.py collectstatic --noinput

gunicorn games_ecommerce.wsgi:application -b 0.0.0.0:8000
