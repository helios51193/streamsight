#!/bin/sh

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Starting Daphne..."
daphne -b 0.0.0.0 -p 8000 analytics_dashboard.asgi:application