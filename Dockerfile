FROM python:3.7-bullseye

RUN apt update && apt install -y ruby-sass \
    && rm -rf /var/lib/apt/lists/*
COPY ./files/start.sh /start.sh
RUN chmod 755 /start.sh
COPY ./files/sso-dashboard.ini /dashboard.ini
RUN chmod 644 /dashboard.ini
RUN pip3 install --upgrade pip
COPY ./requirements.txt /dashboard/
RUN pip3 install -r /dashboard/requirements.txt
RUN pip3 install pyOpenSSL==17.3.0 --upgrade
RUN pip3 install cryptography==2.0 --upgrade
COPY ./dashboard/ /dashboard/
RUN chmod 750 -R /dashboard
RUN rm /dashboard/static/css/gen/all.css \
    /dashboard/static/js/gen/packed.js \
    /dashboard/data/apps.yml-etag 2& > /dev/null
RUN mkdir -p /dashboard/static/img/logos

ENTRYPOINT ["/start.sh"]
