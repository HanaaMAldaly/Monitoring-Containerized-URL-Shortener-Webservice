# Monitoring Containerized URL Shortener Webservice
## Description
Webservice project that shortens URLs, stores the  mapping, and handles redirects by coping the link or scan the QR code, also it provides a detailed dashboard for the shorten urls.
## Project Scope
This project involves creating a webservice that shortens URLs, stores the  mapping, and handles redirects. You will then instrument this service to expose custom  performance metrics. Finally, you will use Prometheus to collect these metrics and Grafana to  build a comprehensive dashboard for visualizing the service's health and usage patterns.
## Technologies
    * Docker
    * Docker Compose
    * Premosthes and Grafana
    * Python
    * [QrCode](https://pypi.org/project/qrcode/)
    * Web framework
    * Postgres database
## Team members
    * Ahmed Kamal
    * Hazem
    * Hanaa Mahmoud
    * Ibrahim Ekram
    * Mahmoud Atwa
## DockerFiles :
    * Dockerfile: builds a lightweight Python 3.11 environment, installs the app dependencies, and copies your project files into the container. It then exposes port 5000 and runs your Flask application using python app.py
    * docker-compose:  runs two services: a Flask web app and a PostgreSQL database, where the web app builds
