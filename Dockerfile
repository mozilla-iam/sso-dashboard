FROM python:3.12-bullseye
ARG RELEASE_NAME

# Install Node.js 18.20.4
RUN apt update && apt install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs=18.20.4-1nodesource1 \
    && rm -rf /var/lib/apt/lists/*

# Install global npm packages
RUN npm install -g sass

# Upgrade pip and install Python dependencies
RUN pip3 install --upgrade pip
COPY ./requirements.txt /dashboard/
RUN pip3 install -r /dashboard/requirements.txt

# Copy the application code
COPY ./dashboard/ /dashboard/

# Create necessary directories and files
RUN mkdir -p /dashboard/data
RUN touch /dashboard/data/apps.yml
RUN chmod 750 -R /dashboard

# Clean up generated files
RUN rm /dashboard/static/css/gen/all.css \
    /dashboard/static/js/gen/packed.js \
    /dashboard/data/apps.yml-etag 2& > /dev/null || true

# Create directory for logos
RUN mkdir -p /dashboard/static/img/logos

# Write the release name to a version file
RUN echo $RELEASE_NAME > /version.json

# Set the entrypoint for the container
ENTRYPOINT ["gunicorn", "dashboard.app:app"]

# This sets the default args which should be overridden
# by cloud deploy. In general, these should match the
# args used in cloud deploy dev environment
CMD ["--worker-class", "gevent", "--bind", "0.0.0.0:8000", "--workers=2", "--max-requests=1000", "--max-requests-jitter=50", "--graceful-timeout=30", "--timeout=60", "--log-level=debug", "--error-logfile=-", "--reload", "--reload-extra-file=/dashboard/data/apps.yml"]
