#!/bin/bash

cd /home/ec2-user/app

aws ecr get-login --region us-west-2 | bash

/usr/local/bin/docker-compose pull
