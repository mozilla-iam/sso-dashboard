FROM python:3-onbuild

RUN mkdir /dashboard

COPY requirements.txt /dashboard/requirements.txt

RUN pip install --upgrade pip

ADD . /dashboard/

WORKDIR /dashboard

