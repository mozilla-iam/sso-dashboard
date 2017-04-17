#!/bin/bash

/etc/init.d/supervisord stop

cp /home/ec2-user/app/conf/supervisor-ansible.ini /etc/supervisord.d/

rm -rf /home/ec2-user/app/*
