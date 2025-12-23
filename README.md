# https://github.com/5CCSACCA/coursework-Armitaeslami/tree/main

# 5CCSACCA Cloud Computing for Artificial Intelligence
## Image-Based Object Detection and Text Generation SaaS

**Student:** Armita Eslami Nazari
**Module:** 5CCSACCA – Cloud Computing for Artificial Intelligence  
**University:** King's College London

---

## Overview

This project is a cloud-based SaaS application developed for the 5CCSACCA coursework. The system takes images as input, detects objects in them using a YOLO model, and generates a short text description using a large language model.

The application is built using a microservices architecture. Each service is containerised using Docker and the whole system is deployed using Docker Compose. The system is exposed through a REST API built with FastAPI.

The project follows the requirements and stages defined in the coursework specification.

---

## System Architecture

The system consists of the following components:

- **API Gateway** – handles incoming requests and authentication
- **YOLO Service** – performs object detection on uploaded images
- **LLM Service** – generates text based on detected objects
- **Postprocessor Service** – processes results asynchronously
- **RabbitMQ** – message queue connecting services
- **MongoDB** – stores request history
- **Firebase Firestore** – stores generated outputs
- **Prometheus and Grafana** – monitoring and metrics

All services run in separate Docker containers and communicate over an internal Docker network.

---

## Main Features

- Image object detection using YOLO11n
- Text generation using BitNet LLM
- REST API built with FastAPI
- Asynchronous processing using RabbitMQ
- Data persistence using MongoDB and Firebase
- Firebase Authentication for user access
- Monitoring using Prometheus and Grafana
- HTTPS using SSL/TLS certificates

---

## Technologies Used

### Programming Language
- Python 3.10+

### Frameworks and Libraries
- FastAPI
- Uvicorn
- Pydantic

### Machine Learning Models
- YOLO11n (Ultralytics)
- BitNet b1.58-2B (Microsoft)

### Databases and Messaging
- MongoDB
- Firebase Firestore
- Firebase Authentication
- RabbitMQ

### Deployment and Monitoring
- Docker
- Docker Compose
- Prometheus
- Grafana

---

## Project Structure

```
coursework/
├── api-gateway/
├── yolo-service/
├── llm-service/
├── postprocessor-service/
├── prometheus/
├── grafana/
├── docker-compose.yml
├── pricing.md
└── README.md
```

---

## Prerequisites

- Docker
- Docker Compose
- Git
- At least 8 GB RAM
- Firebase project with Firestore and Authentication enabled

---

## Setup and Deployment

### Clone the Repository

```bash
git clone <repository-url>
cd coursework
```

### Firebase Setup

1. Create a Firebase project
2. Enable Firestore and Authentication
3. Download the service account key
4. Save it as `firebase_key.json` inside `api-gateway/app/`

### SSL Certificates

```bash
cd api-gateway
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365
cd ..
```

### Build and Run the System

```bash
docker-compose build
docker-compose up -d
```

---

## API Overview

**Base URL:**
```
https://localhost:8000
```

**Authentication:**
```
Authorization: Bearer <Firebase ID Token>
```

**Main endpoints:**
- `GET /health`
- `POST /detect`
- `POST /describe`
- `POST /generate`
- `GET /history`
- `GET /firebase/history`
- `GET /stories`
- `GET /metrics`

---

## Data Storage

- **MongoDB** is used to store request history and results
- **Firebase Firestore** stores generated outputs and supports update and delete operations

---

## Testing

Each service includes basic unit and integration tests.

Tests can be run inside the containers using:

```bash
docker exec <service-name> pytest
```

---

## Monitoring

- **Prometheus** collects metrics from all services
- **Grafana** is used to visualise request rates, latency, CPU usage, and memory usage
- **RabbitMQ** provides a management UI for inspecting queues

---

## Security

The following security measures are implemented:

- HTTPS using SSL/TLS
- Firebase Authentication
- Rate limiting
- Input validation
- Docker network isolation
- Credentials excluded from version control

---

## Cost Estimation

Infrastructure cost estimation is provided in `pricing.md`, including assumptions and scalability considerations, as required by the coursework.

---

## Limitations

- The system runs on CPU-only infrastructure, which affects performance
- LLM inference introduces noticeable latency
- Self-signed certificates are used for development

---

## Coursework Coverage

This project covers all required coursework stages, including model deployment, containerisation, API development, persistence, messaging, authentication, monitoring, testing, security, and cost estimation.

---

## Author

**Armita Eslami Nazari**  
King's College London