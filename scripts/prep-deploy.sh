#!/bin/bash

cd /home/ec2-user/app

# Clear the old containers
/usr/local/bin/docker-compose stop
/usr/local/bin/docker-compose rm -f

rm -rf /home/ec2-user/app

mkdir -p /home/ec2-user/app

#Grab an ECR Login
aws ecr get-login --region us-west-2 | bash
