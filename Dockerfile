FROM centos:7

RUN yum update -y
RUN yum install epel-release -y && yum update -y
RUN yum install nginx python36 python36-devel python36-pip -y
COPY ./ansible/roles/dashboard/files/dumb-init /usr/bin/dumb-init
RUN chmod 775 /usr/bin/dumb-init
RUN yum install gcc \
    libffi-devel \
    \ openssl openssl-devel \
    curl-devel -y
COPY ./ansible/roles/dashboard/files/nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./ansible/roles/dashboard/files/nginx/start.sh /usr/bin/start.sh
RUN chmod 775 /usr/bin/start.sh
COPY ./ansible/roles/dashboard/files/sso-dashboard.ini /etc/dashboard.ini
RUN chmod 775 /etc/dashboard.ini
RUN yum install git -y
RUN yum install rubygem-sass -y
RUN pip3 install --upgrade setuptools-rust pip
RUN pip3 install credstash
RUN useradd -ms /bin/bash flaskuser
RUN mkdir /dashboard
RUN chown -R flaskuser /dashboard
COPY requirements.txt /dashboard/requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r /dashboard/requirements.txt
COPY ./dashboard/ /dashboard/
RUN rm /dashboard/static/css/gen/all.css 2& > /dev/null
RUN rm /dashboard/static/js/gen/packed.js 2& > /dev/null
RUN rm /dashboard/data/apps.yml-etag 2& > /dev/null
RUN mkdir -p /dashboard/static/img/logos
RUN chmod 750 -R /dashboard
RUN useradd -ms /bin/bash flaskapp
RUN chown -R flaskapp:nginx /dashboard
RUN pip3 install pyOpenSSL==17.3.0 --upgrade
RUN pip3 install cryptography==2.0 --upgrade
RUN pip3 install flake8 --upgrade
# RUN pip3 install git+git://github.com/mozilla-iam/pyoidc.git@fix_updated_at#egg=pyoidc
ENTRYPOINT [ "dumb-init", "/usr/bin/start.sh" ]
