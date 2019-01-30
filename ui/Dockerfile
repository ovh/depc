FROM node:8.9.1

WORKDIR /app

# Install base debian packages
RUN apt-get update \
        && apt-get install -y nginx

# Redirect logs to stdout and stderr
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
        && ln -sf /dev/stderr /var/log/nginx/error.log

# Install npm packages
COPY package.json /app/package.json

RUN npm install \
        && npm install bower -g \
        && npm install grunt-cli -g \
        && npm install grunt -g

COPY nginx/default /etc/nginx/sites-enabled/default

# Install bower components
COPY bower.json /app/bower.json

RUN bower install --allow-root

# Copy the source fles
COPY app app

# Build the app
COPY Gruntfile.js /app/Gruntfile.js

# Build HTML/CSS/JS
RUN grunt build \
        && mv /app/dist/* /var/www/html

# Start web server
EXPOSE 80
CMD ["/usr/sbin/nginx", "-g", "daemon off;"]
