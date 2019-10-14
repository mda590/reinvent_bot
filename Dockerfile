FROM ubuntu:latest

RUN apt-get update
RUN apt-get install -y
RUN apt-get install -y unzip wget apt-transport-https gnupg2 \
      locales python3-pip python3-dev \
      libpq-dev libxml2-dev libxslt-dev libfreetype6-dev libffi-dev git curl vim

# Download and install Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install

# Download and Unzip Chrome Driver Binary
RUN wget -O /tmp/chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/2.44/chromedriver_linux64.zip
RUN unzip -o -d /usr/bin /tmp/chromedriver_linux64.zip

RUN mkdir /reinvent_bot
COPY ./ /reinvent_bot/
RUN pip3 install -r /reinvent_bot/requirements.txt

WORKDIR /reinvent_bot
