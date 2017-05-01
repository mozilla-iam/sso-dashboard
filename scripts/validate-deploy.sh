#!/bin/bash

sleep 60

result=$(curl -s http://localhost:8000/)

if [[ "$result" =~ "Mozilla SSO Dashboard" ]]; then
    echo "The system is up."
    exit 0
else
    echo "The system is not up"
    exit 1
fi
