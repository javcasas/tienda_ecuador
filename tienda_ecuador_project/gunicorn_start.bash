#!/bin/bash

NAME="facturacion_dssti"                                  # Name of the application
DJANGODIR=/home/protected/django # Django project directory
SOCKFILE=/home/protected/django/run/gunicorn.sock  # we will communicte using this unix socket
USER=hello                                        # the user to run as
GROUP=webapps                                     # the group to run as
NUM_WORKERS=3                                     # how many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=tienda_ecuador_project.settings             # which settings file should Django use
DJANGO_WSGI_MODULE=tienda_ecuador_project.wsgi                     # WSGI module name

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR
. $DJANGODIR/../venv/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec ../venv/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --bind=unix:$SOCKFILE \
  --bind=0.0.0.0:18001 \
  --log-level=debug \
  --log-file=-
