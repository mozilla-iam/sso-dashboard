#!/bin/bash
exec python3 -m gunicorn.app.wsgiapp dashboard.app:app --worker-class gevent --bind 0.0.0.0:8000 --workers=${DASHBOARD_GUNICORN_WORKERS:-5} --reload
