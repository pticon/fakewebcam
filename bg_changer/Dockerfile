#
# Debian (buster) Dockerfile
#
# Create an build environment Dockerfile on top of debian with
# * node
# * tensorflow
# * bodypix
# * ini
#
# Build:
# docker build --tag bg_changer .
#
# Run:
# docker run -ti --rm bg_changer
#

# Pull base image
FROM debian:buster

# Install what we need
RUN apt update && \
	apt install -y wget make build-essential && \
	wget -qO- http://deb.nodesource.com/setup_14.x | bash - && \
	apt install -y nodejs && \
	mkdir /.npm && \
	chmod 777 /.npm
	#rm -rf /var/lib/apt/lists/*

# Copy the bodypix package description and install it
WORKDIR /src
COPY package.json /src
RUN npm install && npm install --save ini

# Copy the app source and make it as the entrypoint
COPY app.js /src
ENTRYPOINT node /src/app.js
