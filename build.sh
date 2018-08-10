#!/bin/sh

mkdir temp_image
mv Dockerfile gmail.py privacy_policy.html requirements.txt temp_image
docker build -t gmail-gettt -t registry.viti.site/gmail-gettt:latest temp_image
mv temp_image/* .
rmdir temp_image
docker push registry.viti.site/gmail-gettt:latest
