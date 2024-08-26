FROM python:3.12-bullseye
ARG RELEASE_NAME

# Install Node.js 18.20.4 and global npm packages in a single layer
RUN apt update && apt install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs=18.20.4-1nodesource1 \
    && npm install -g sass \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, install Python dependencies, and clean up in a single layer
COPY ./requirements.txt /dashboard/
RUN pip3 install --upgrade pip \
    && pip3 install -r /dashboard/requirements.txt

# Copy the dashboard code and create necessary directories and files
COPY ./dashboard/ /dashboard/
RUN mkdir -p /dashboard/data /dashboard/static/img/logos \
    && touch /dashboard/data/apps.yml \
    && chmod 750 -R /dashboard \
    && rm /dashboard/static/css/gen/all.css \
    /dashboard/static/js/gen/packed.js \
    /dashboard/data/apps.yml-etag 2>/dev/null || true

# Write the release name to a version file
RUN echo $RELEASE_NAME > /version.json

# Set the entrypoint for the container
ENTRYPOINT ["gunicorn", "dashboard.app:app"]

# This sets the default args which should be overridden
# by cloud deploy. In general, these should match the
# args used in cloud deploy dev environment
# Default command arguments
CMD ["--worker-class=gevent", "--bind=0.0.0.0:8000", "--workers=3", "--graceful-timeout=30", "--timeout=60", "--log-config=dashboard/logging.ini", "--reload", "--reload-extra-file=/dashboard/data/apps.yml"]
