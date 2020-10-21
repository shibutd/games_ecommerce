#!/bin/bash

python manage.py migrate

python manage.py collectstatic

python gunicorn games_ecommerce.wsgi -b 0.0.0.0:8000
