# Monitoring Containerized URL Shortener Webservice

A containerized URL-shortening web service built with Python and Docker, integrated with Prometheus and Grafana for full monitoring, metrics collection, and performance visualization.

---

## 📌 Overview

This project provides a complete URL-Shortener web service that allows users to:

- Shorten long URLs  
- Redirect using a generated short URL  
- Generate QR codes for shortened URLs  
- Store URL mappings in a PostgreSQL database  
- Export custom metrics for monitoring  
- Visualize service performance using Grafana dashboards

The entire application is containerized using Docker and orchestrated with Docker Compose.

---

## 🚀 Features

- URL shortening & redirect functionality  
- PostgreSQL-based persistent storage  
- QR code generation  
- Fully containerized environment  
- Prometheus integration for metric scraping  
- Grafana dashboards for real-time visualization  
- Custom application metrics:
  - Total requests  
  - Response latency  
  - Shortened URLs count  
  - Redirect count  
  - Error counts  

---

## 🛠️ Technologies Used

- **Python**
- **Flask**
- **PostgreSQL**
- **Docker & Docker Compose**
- **Prometheus**
- **Grafana**
- **qrcode** Python library

---

## 📂 Project Structure

Monitoring-Containerized-URL-Shortener-Webservice/
├── .github/
│   └── workflows/
│       └── docker-image.yml
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── templates/
├── static/
├── prometheus/
└── grafana/

---

## 🧰 Setup & Installation

### Prerequisites
- Docker  
- Docker Compose  
- Git  

---

## ▶️ Running the Project

# Clone the repository:

```bash
git clone https://github.com/HanaaMAldaly/Monitoring-Containerized-URL-Shortener-Webservice.git
cd Monitoring-Containerized-URL-Shortener-Webservice
```

# Build & run all services:
```bash
docker-compose up --build
```
it will run on http://localhost:5000

## 🐳 DockerFiles :
    * Dockerfile: builds a lightweight Python 3.11 environment, installs the app dependencies, and copies your project files into the container. It then exposes port 5000 and runs your Flask application using python app.py
    * docker-compose:  runs two services: a Flask web app and a PostgreSQL database, where the web app builds

## 🏭 Deployment
Cloud AWS

## Team members
    * Ahmed Kamal
    * Hazem
    * Hanaa Mahmoud
    * Ibrahim Ekram
    * Mahmoud Atwa

