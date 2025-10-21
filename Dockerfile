FROM node:22-alpine3.22 AS nodebuild
RUN npm install -g sass

FROM python:3.12-alpine3.22 AS pythonbuild
RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    apk add gcc musl-dev libffi-dev \
    && pip3 install --upgrade pip \
    && pip3 install -r requirements.txt

FROM python:3.12-alpine3.22
ARG RELEASE_NAME

COPY --from=nodebuild /usr/lib /usr/lib
COPY --from=nodebuild /usr/local/lib /usr/local/lib
COPY --from=nodebuild /usr/local/bin /usr/local/bin
COPY --from=pythonbuild /usr/lib /usr/lib
COPY --from=pythonbuild /usr/local/lib /usr/local/lib
COPY --from=pythonbuild /usr/local/bin /usr/local/bin

COPY ./dashboard/ /dashboard/
RUN addgroup -S dashboard \
    && adduser -SG dashboard dashboard \
    && rm -f /dashboard/static/css/gen/all.css /dashboard/static/js/gen/packed.js /dashboard/data/apps.yml-etag \
    && mkdir -p /dashboard/data /dashboard/static/img/logos \
    && touch /dashboard/data/apps.yml \
    && chown -R dashboard:dashboard /dashboard/data \
    && chown -R dashboard:dashboard /dashboard/static \
    && echo $RELEASE_NAME > /version.json

USER dashboard

# Set the entrypoint for the container
ENTRYPOINT ["gunicorn", "dashboard.app:app"]

# This sets the default args which should be overridden
# by cloud deploy. In general, these should match the
# args used in cloud deploy dev environment
# Default command arguments
CMD ["--worker-class=gevent", "--bind=0.0.0.0:8000", "--workers=3", "--graceful-timeout=30", "--timeout=60", "--log-config=dashboard/logging.ini", "--reload", "--reload-extra-file=/dashboard/data/apps.yml"]
