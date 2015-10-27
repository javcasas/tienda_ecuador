#!/bin/sh
. venv/bin/activate
cd django && exec python manage.py runserver
