FROM ubuntu:latest

RUN apt-get update
RUN apt-get install -y
RUN apt-get install -y unzip wget apt-transport-https gnupg2 \
      locales python3-pip python3-dev 

RUN mkdir /reinvent_bot
COPY ./ /reinvent_bot/
RUN pip3 install -r /reinvent_bot/requirements.txt

WORKDIR /reinvent_bot
