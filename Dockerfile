FROM python:3.12-bullseye
ARG RELEASE_NAME

RUN apt update && apt install -y nodejs npm \
    && rm -rf /var/lib/apt/lists/*
RUN npm install -g sass
COPY ./files/start.sh /start.sh
RUN chmod 755 /start.sh
RUN pip3 install --upgrade pip
COPY ./requirements.txt /dashboard/
RUN pip3 install -r /dashboard/requirements.txt
COPY ./dashboard/ /dashboard/
RUN chmod 750 -R /dashboard
RUN rm /dashboard/static/css/gen/all.css \
    /dashboard/static/js/gen/packed.js \
    /dashboard/data/apps.yml-etag 2& > /dev/null
RUN mkdir -p /dashboard/static/img/logos
RUN echo $RELEASE_NAME > /version.json

ENTRYPOINT ["/start.sh"]
