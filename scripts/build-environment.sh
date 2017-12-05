#!/bin/bash

#Clean up old images
docker images -q |xargs docker rmi

cd /home/ec2-user/app

ACCOUNT_ID=`aws sts get-caller-identity | grep Account | cut -d '"' -f4`

sed -i s/656532927350/${ACCOUNT_ID}/g docker-compose.yml

aws ecr get-login --region us-west-2 --no-include-email | bash

/usr/local/bin/docker-compose pull
