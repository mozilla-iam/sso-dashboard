#!/bin/bash

cd /home/ec2-user/app

# Clear the old containers
/usr/local/bin/docker-compose stop
/usr/local/bin/docker-compose rm -f

# rm -rf /home/ec2-user/app

# mkdir -p /home/ec2-user/app

#Grab an ECR Login
aws ecr get-login --region us-west-2 | bash

#Pull the latest version of the container
docker pull 656532927350.dkr.ecr.us-west-2.amazonaws.com/sso-dashboard:latest
