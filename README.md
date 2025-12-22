# Cloud Computing AI SaaS - YOLO Object Detection & Story Generation

**Course:** 5CCSACCA Cloud Computing for Artificial Intelligence  
**Student:** Armita Eslami  
**Project:** AI-powered Image Analysis with Object Detection and Story Generation

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [API Endpoints](#api-endpoints)
- [Security](#security)
- [Monitoring](#monitoring)
- [Testing](#testing)
- [Cost Estimation](#cost-estimation)
- [Troubleshooting](#troubleshooting)
- [Stage-by-Stage Implementation](#stage-by-stage-implementation)

---

## 🎯 Overview

This project is a cloud-based AI SaaS application that combines YOLO object detection with BitNet LLM to analyze images and generate creative stories. Users upload images, the system detects objects using YOLO11n, generates descriptive stories using BitNet LLM, and stores results in both MongoDB and Firebase Firestore.

### Key Capabilities:
- **Real-time object detection** using YOLO11n
- **AI-powered story generation** using BitNet 1.58-bit LLM
- **Dual database persistence** (MongoDB + Firebase)
- **Asynchronous processing** via RabbitMQ
- **Secure HTTPS** communication with SSL/TLS
- **Comprehensive monitoring** with Prometheus & Grafana
- **User authentication** via Firebase Auth
- **RESTful API** with FastAPI

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway (HTTPS)                      │
│                    FastAPI + Firebase Auth                       │
│                         Port 8000 (SSL)                          │
└────────┬──────────────────────────────────────────┬─────────────┘
         │                                           │
    ┌────▼─────┐                               ┌────▼─────┐
    │  YOLO    │                               │   LLM    │
    │ Service  │                               │ Service  │
    │ (YOLO11n)│                               │ (BitNet) │
    │Port 8001 │                               │Port 8002 │
    └──────────┘                               └──────────┘
         │                                           │
         └───────────────┬───────────────────────────┘
                         │
                    ┌────▼─────┐
                    │ RabbitMQ │
                    │  Queue   │
                    │Port 5672 │
                    └────┬─────┘
                         │
                    ┌────▼──────────┐
                    │ Postprocessor │
                    │   Service     │
                    └───────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼─────┐   ┌────▼─────┐   ┌────▼─────────┐
    │ MongoDB  │   │ Firebase │   │ Prometheus   │
    │Port 27017│   │Firestore │   │ + Grafana    │
    └──────────┘   └──────────┘   │Port 9090/3000│
                                   └──────────────┘
```

### Workflow:
1. **User uploads image** → API Gateway (authenticated)
2. **YOLO detection** → Identifies objects in image
3. **LLM generation** → Creates descriptive story
4. **Database storage** → Saves to MongoDB & Firebase
5. **Queue processing** → Publishes to RabbitMQ
6. **Postprocessing** → Enhances and stores final results
7. **Monitoring** → Prometheus collects metrics → Grafana visualizes

---

## ✨ Features

### Core Functionality
- ✅ Object detection using YOLO11n (80 COCO classes)
- ✅ Story generation using BitNet 1.58-bit LLM
- ✅ Dual-database persistence (MongoDB + Firebase Firestore)
- ✅ Asynchronous message processing (RabbitMQ)
- ✅ RESTful API with comprehensive endpoints

### Security (Stage 11)
- ✅ SSL/TLS encryption (HTTPS)
- ✅ Firebase authentication & authorization
- ✅ Rate limiting (100 requests/minute)
- ✅ Input validation & file type verification
- ✅ CORS configuration
- ✅ Isolated Docker network

### Monitoring (Stage 9)
- ✅ Prometheus metrics collection
- ✅ Grafana dashboards for visualization
- ✅ Request rate, latency, and throughput tracking
- ✅ CPU and memory usage monitoring
- ✅ RabbitMQ queue management UI

### DevOps
- ✅ Docker containerization for all services
- ✅ Docker Compose orchestration
- ✅ Health checks for all services
- ✅ Automatic service restart policies
- ✅ Volume persistence for databases

---

## 🛠️ Technology Stack

### AI/ML Models
- **YOLO11n** - Object detection (Ultralytics)
- **BitNet b1.58-2B** - 1.58-bit quantized LLM (Microsoft)

### Backend
- **FastAPI** - API framework
- **Python 3.10/3.11** - Programming language
- **Uvicorn** - ASGI server with SSL/TLS support

### Databases
- **MongoDB** - Primary data storage
- **Firebase Firestore** - Cloud-based document database
- **Firebase Auth** - User authentication

### Message Queue
- **RabbitMQ** - Asynchronous task processing

### Monitoring
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization
- **prometheus-client** - Python instrumentation

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **OpenSSL** - SSL/TLS certificate generation

### Additional Libraries
- **Pydantic** - Data validation
- **Pika** - RabbitMQ Python client
- **httpx** - HTTP client for service communication
- **slowapi** - Rate limiting middleware
- **python-multipart** - File upload handling

---

## 📁 Project Structure

```
coursework/
├── api-gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── cert.pem                    # SSL certificate
│   ├── key.pem                     # SSL private key
│   └── app/
│       ├── main.py                 # Main API application
│       ├── db_service.py           # MongoDB operations
│       ├── firebase_service.py     # Firebase operations
│       ├── rabbitmq_service.py     # RabbitMQ publisher
│       ├── firebase_key.json       # Firebase credentials
│       └── __init__.py
├── yolo-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 # YOLO detection service
│       └── __init__.py
├── llm-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 # BitNet LLM service
│       └── __init__.py
├── postprocessor-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 # RabbitMQ consumer
│       └── __init__.py
├── prometheus/
│   └── prometheus.yml              # Prometheus configuration
├── grafana/
│   └── provisioning/               # Grafana datasources
├── docker-compose.yml              # Orchestration configuration
├── pricing.md                      # Cost estimation (Stage 8)
├── .gitignore
└── README.md                       # This file
```

---

## 📋 Prerequisites

- **Docker** (v20.10+)
- **Docker Compose** (v2.0+)
- **Git**
- **8GB+ RAM** (for BitNet LLM)
- **10GB+ disk space**
- **Firebase Project** with Firestore and Authentication enabled

---

## 🚀 Installation & Setup

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd coursework
```

### Step 2: Firebase Setup

1. Create a Firebase project at https://console.firebase.google.com
2. Enable **Firestore Database** and **Authentication**
3. Download service account key as `firebase_key.json`
4. Place it in `api-gateway/app/firebase_key.json`

### Step 3: Generate SSL Certificates

#### Option A: Using Docker (Recommended for Windows)
```bash
docker run --rm -v ${PWD}/api-gateway:/certificates alpine/openssl req -x509 -newkey rsa:4096 -nodes -out /certificates/cert.pem -keyout /certificates/key.pem -days 365 -subj "/C=GB/ST=London/L=London/O=KCL/CN=localhost"
```

#### Option B: Using OpenSSL (Linux/Mac/Git Bash)
```bash
cd api-gateway
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
cd ..
```

**Note:** For production, use certificates from a trusted CA (e.g., Let's Encrypt).

### Step 4: Build and Start Services

```bash
# Build all containers
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 5: Verify Services

```bash
# API Gateway (HTTPS)
curl -k https://localhost:8000/health

# YOLO Service
curl http://localhost:8001/health

# LLM Service
curl http://localhost:8002/health

# Prometheus
curl http://localhost:9090/-/healthy

# RabbitMQ Management
# Open http://localhost:15672 (guest/guest)

# Grafana
# Open http://localhost:3000 (admin/admin)
```

---

## 🔌 API Endpoints

### Base URL
```
https://localhost:8000
```

### Authentication
All protected endpoints require Firebase ID token:
```bash
Authorization: Bearer <firebase-id-token>
```

### Endpoints

#### 1. Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "yolo_service": "healthy",
  "llm_service": "healthy",
  "mongodb": "connected",
  "rabbitmq": "connected"
}
```

---

#### 2. Object Detection (Lightweight)
```http
POST /detect
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Parameters:**
- `file`: Image file (JPG, PNG, WEBP)

**Response:**
```json
{
  "objects": {
    "person": 2,
    "car": 1,
    "dog": 1
  },
  "message": "Sent to RabbitMQ for post-processing"
}
```

---

#### 3. Image Description (Full Pipeline)
```http
POST /describe
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Parameters:**
- `file`: Image file (JPG, PNG, WEBP)

**Response:**
```json
{
  "objects": {
    "person": 2,
    "car": 1
  },
  "description": "In a sunny park, two people are enjoying a day out with their car parked nearby...",
  "message": "Sent to RabbitMQ for post-processing"
}
```

---

#### 4. LLM Story Generation
```http
POST /generate
Authorization: Bearer <token>
Content-Type: application/json
```

**Body:**
```json
{
  "objects": {
    "person": 2,
    "dog": 1
  }
}
```

**Response:**
```json
{
  "description": "Two friends walked their playful dog through the bustling city streets..."
}
```

---

#### 5. MongoDB History
```http
GET /history?limit=10&skip=0
Authorization: Bearer <token>
```

**Response:**
```json
{
  "records": [
    {
      "_id": "...",
      "user_id": "user123",
      "objects": {"person": 2},
      "description": "...",
      "timestamp": "2025-12-21T10:30:00Z"
    }
  ],
  "count": 1
}
```

---

#### 6. Firebase History
```http
GET /firebase/history?limit=100
Authorization: Bearer <token>
```

**Response:**
```json
{
  "records": [
    {
      "id": "firebase-doc-id",
      "user_id": "user123",
      "objects": {"car": 1},
      "description": "...",
      "timestamp": "2025-12-21T10:30:00Z"
    }
  ],
  "count": 1
}
```

---

#### 7. Update Firebase Record
```http
PUT /firebase/update/{document_id}
Authorization: Bearer <token>
Content-Type: application/json
```

**Body:**
```json
{
  "description": "Updated description text"
}
```

---

#### 8. Delete Firebase Record
```http
DELETE /firebase/delete/{document_id}
Authorization: Bearer <token>
```

---

#### 9. Postprocessed Stories
```http
GET /stories?limit=10&skip=0
Authorization: Bearer <token>
```

**Response:**
```json
{
  "records": [
    {
      "_id": "...",
      "original_id": "...",
      "story": "Enhanced story generated by postprocessor...",
      "processed_at": "2025-12-21T10:35:00Z"
    }
  ],
  "count": 1
}
```

---

#### 10. Metrics (Prometheus)
```http
GET /metrics
```

**Response:** Prometheus-formatted metrics
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{endpoint="/detect",method="POST",status="success"} 42.0
...
```

---

## 🔒 Security

### Stage 11: Security Implementation

#### 1. SSL/TLS Encryption
All API communication is encrypted using SSL/TLS certificates.

**Certificate Location:** 
- `api-gateway/cert.pem` (public certificate)
- `api-gateway/key.pem` (private key)

**Generation:**
```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365
```

**Production Recommendations:**
- Use Let's Encrypt for free CA-signed certificates
- Configure nginx as reverse proxy with SSL termination
- Enable HTTPS redirects (HTTP → HTTPS)
- Use strong cipher suites (TLS 1.2+)
- Implement HSTS headers

#### 2. Authentication & Authorization
- **Firebase Authentication** for user identity
- **ID Token verification** on all protected endpoints
- **User-scoped data access** (users only see their own data)

#### 3. Rate Limiting
- **100 requests per minute** per IP address
- Implemented using `slowapi` middleware
- Prevents API abuse and DDoS attacks

#### 4. Input Validation
- **File type validation** (only JPG, PNG, WEBP)
- **File size limits** to prevent memory exhaustion
- **Request body validation** using Pydantic models

#### 5. Network Isolation
- **Docker network** isolates services
- Internal services not exposed to host
- Only API Gateway accessible from outside

#### 6. CORS Configuration
- Configured for specific origins (production)
- Prevents unauthorized cross-origin requests

#### 7. Secrets Management
- Firebase credentials in mounted volume (not in image)
- Environment variables for configuration
- `.gitignore` prevents credential commits

**Testing SSL:**
```bash
# Development (self-signed certificate)
curl -k https://localhost:8000/health

# Production (CA-signed certificate)
curl https://yourdomain.com/health
```

---

## 📊 Monitoring

### Stage 9: Monitoring Implementation

#### Prometheus (Metrics Collection)
**URL:** http://localhost:9090

**Available Metrics:**
- `api_requests_total` - Total API requests by endpoint, method, status
- `api_request_latency_seconds` - Request duration histogram
- `process_cpu_seconds_total` - CPU usage
- `process_resident_memory_bytes` - Memory usage
- `up` - Service health status

**Configuration:** `prometheus/prometheus.yml`

**Scrape Interval:** 15 seconds

**Targets:**
- API Gateway (HTTPS with `insecure_skip_verify`)
- YOLO Service
- LLM Service

**Accessing Prometheus:**
```bash
# Open Prometheus UI
open http://localhost:9090

# Check targets status
open http://localhost:9090/targets

# Example query
open http://localhost:9090/graph
# Query: rate(api_requests_total[5m])
```

---

#### Grafana (Visualization)
**URL:** http://localhost:3000  
**Default Credentials:** admin / admin

**Setup:**
1. Login to Grafana
2. Add Prometheus data source:
   - URL: `http://prometheus:9090`
   - Click "Save & Test"
3. Import dashboard or create panels

**Recommended Queries:**

**Total Requests:**
```promql
sum(api_requests_total{status="success"})
```

**Request Rate:**
```promql
rate(api_requests_total{status="success"}[5m])
```

**Average Latency:**
```promql
rate(api_request_latency_seconds_sum[5m]) / 
rate(api_request_latency_seconds_count[5m])
```

**95th Percentile Latency:**
```promql
histogram_quantile(0.95, 
  rate(api_request_latency_seconds_bucket[5m]))
```

**CPU Usage:**
```promql
rate(process_cpu_seconds_total{job="api-gateway"}[5m])
```

**Memory Usage (MB):**
```promql
process_resident_memory_bytes{job="api-gateway"} / 1024 / 1024
```

---

#### RabbitMQ Management UI
**URL:** http://localhost:15672  
**Credentials:** guest / guest

**Features:**
- Queue monitoring
- Message rates
- Consumer connections
- Exchange management

---

## 🧪 Testing

### Manual Testing

#### Test Object Detection
```bash
curl -k -X POST https://localhost:8000/detect \
  -H "Authorization: Bearer <your-firebase-token>" \
  -F "file=@test-image.jpg"
```

#### Test Story Generation
```bash
curl -k -X POST https://localhost:8000/describe \
  -H "Authorization: Bearer <your-firebase-token>" \
  -F "file=@test-image.jpg"
```

#### Test History Retrieval
```bash
# MongoDB
curl -k https://localhost:8000/history \
  -H "Authorization: Bearer <your-firebase-token>"

# Firebase
curl -k https://localhost:8000/firebase/history \
  -H "Authorization: Bearer <your-firebase-token>"
```

#### Load Testing
```bash
# Generate 100 requests
for i in {1..100}; do
  curl -k https://localhost:8000/health
  sleep 0.1
done
```

### Automated Testing

Test files are located in each service's `app/` directory.

**Run tests:**
```bash
# API Gateway tests
docker exec api-gateway pytest app/tests/

# YOLO Service tests
docker exec yolo-service pytest app/tests/

# LLM Service tests
docker exec llm-service pytest app/tests/
```

---

## 💰 Cost Estimation

See [pricing.md](pricing.md) for detailed cost analysis.

### Summary (Monthly Costs for 10,000 requests/month)

| Service | Provider | Cost |
|---------|----------|------|
| Compute (API + Workers) | AWS EC2 t3.medium | $30.40 |
| GPU Compute (ML Models) | AWS EC2 g4dn.xlarge | $111.70 |
| MongoDB Atlas | M10 Dedicated | $57.00 |
| Firebase Firestore | Pay-as-you-go | $0.50 |
| RabbitMQ (CloudAMQP) | Bunny Plan | $0.00 (Free) |
| Load Balancer | AWS ALB | $16.20 |
| SSL Certificate | Let's Encrypt | $0.00 (Free) |
| Monitoring | Grafana Cloud | $0.00 (Free tier) |
| **Total** | | **~$215.80/month** |

**Note:** Costs scale with usage. GPU instances are the largest expense.

---

## 🐛 Troubleshooting

### Common Issues

#### 1. API Gateway Container Fails to Start

**Symptom:** Container exits immediately

**Solution:**
```bash
# Check logs
docker-compose logs api-gateway

# Verify certificates exist
ls api-gateway/cert.pem api-gateway/key.pem

# Regenerate certificates if missing
docker run --rm -v ${PWD}/api-gateway:/certificates alpine/openssl \
  req -x509 -newkey rsa:4096 -nodes \
  -out /certificates/cert.pem -keyout /certificates/key.pem \
  -days 365 -subj "/C=GB/ST=London/L=London/O=KCL/CN=localhost"
```

---

#### 2. Prometheus Can't Scrape API Gateway

**Symptom:** API Gateway shows as DOWN in http://localhost:9090/targets

**Solution:**
Verify `prometheus/prometheus.yml` has HTTPS configuration:
```yaml
- job_name: 'api-gateway'
  scheme: https
  tls_config:
    insecure_skip_verify: true
  static_configs:
    - targets: ['api-gateway:8000']
```

Restart Prometheus:
```bash
docker-compose restart prometheus
```

---

#### 3. RabbitMQ Connection Refused

**Symptom:** Services can't connect to RabbitMQ

**Solution:**
```bash
# Check RabbitMQ is running
docker-compose ps rabbitmq

# Check logs
docker-compose logs rabbitmq

# Restart RabbitMQ
docker-compose restart rabbitmq

# Wait for RabbitMQ to be ready
sleep 10
docker-compose restart api-gateway postprocessor-service
```

---

#### 4. MongoDB Connection Issues

**Symptom:** "Connection refused" or "No route to host"

**Solution:**
```bash
# Verify MongoDB is running
docker-compose ps mongodb

# Check MongoDB logs
docker-compose logs mongodb

# Restart services
docker-compose restart mongodb
sleep 5
docker-compose restart api-gateway postprocessor-service
```

---

#### 5. Firebase Authentication Errors

**Symptom:** 401 Unauthorized responses

**Solution:**
1. Verify `firebase_key.json` is in `api-gateway/app/`
2. Check Firebase project settings
3. Ensure token is valid and not expired
4. Check API Gateway logs for Firebase initialization:
   ```bash
   docker-compose logs api-gateway | grep -i firebase
   ```

---

#### 6. Out of Memory (BitNet LLM)

**Symptom:** LLM service crashes or slow responses

**Solution:**
```bash
# Increase Docker memory limit to 8GB+
# Docker Desktop → Settings → Resources → Memory

# Check memory usage
docker stats llm-service
```

---

#### 7. Port Already in Use

**Symptom:** "Bind for 0.0.0.0:8000 failed: port is already allocated"

**Solution:**
```bash
# Find process using port
# Windows:
netstat -ano | findstr :8000

# Linux/Mac:
lsof -i :8000

# Kill the process or change port in docker-compose.yml
```

---

#### 8. SSL Certificate Errors in Browser

**Symptom:** "Your connection is not private" warning

**Solution:**
This is expected with self-signed certificates. For testing:
- Click "Advanced" → "Proceed to localhost (unsafe)"
- Or use `curl -k` flag to bypass SSL verification

For production, use CA-signed certificates (Let's Encrypt).

---

### Service Health Checks

```bash
# Check all services
docker-compose ps

# Check specific service logs
docker-compose logs -f <service-name>

# Restart all services
docker-compose restart

# Rebuild and restart specific service
docker-compose build <service-name>
docker-compose up -d <service-name>

# Clean restart (removes volumes)
docker-compose down -v
docker-compose up -d
```

---

## 📚 Stage-by-Stage Implementation

### Stage 1: Model Integration
- ✅ Implemented YOLO11n for object detection
- ✅ Integrated BitNet b1.58-2B LLM for text generation
- ✅ Default model parameters configured

### Stage 2: Containerization
- ✅ Created Dockerfiles for all services
- ✅ Multi-stage builds for optimization
- ✅ Dependencies managed via requirements.txt

### Stage 3: API Development
- ✅ FastAPI framework for REST API
- ✅ Multiple endpoints for different functionalities
- ✅ Swagger UI auto-generated documentation

### Stage 4: Database Persistence
- ✅ MongoDB integration for primary storage
- ✅ GET endpoint for history retrieval
- ✅ Unique record IDs and timestamps

### Stage 5: Firebase Integration
- ✅ Firestore database for cloud storage
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Firebase Admin SDK integration

### Stage 6: Message Queue & Orchestration
- ✅ RabbitMQ for asynchronous processing
- ✅ Postprocessor service as message consumer
- ✅ Docker Compose for multi-container deployment

### Stage 7: Authentication
- ✅ Firebase Authentication integration
- ✅ ID token verification on protected endpoints
- ✅ User-scoped data access

### Stage 8: Cost Estimation
- ✅ Detailed pricing analysis in pricing.md
- ✅ AWS, Firebase, MongoDB cost breakdown
- ✅ Scaling considerations documented

### Stage 9: Monitoring
- ✅ Prometheus metrics collection
- ✅ Grafana dashboards for visualization
- ✅ Custom metrics for API requests, latency, CPU, memory

### Stage 10: Testing
- ✅ Unit tests for individual services
- ✅ Integration test scenarios
- ✅ Manual testing documentation

### Stage 11: Security
- ✅ SSL/TLS encryption (HTTPS)
- ✅ Self-signed certificates for development
- ✅ Rate limiting middleware
- ✅ Input validation and sanitization
- ✅ CORS configuration
- ✅ Network isolation via Docker

---

## 📖 Documentation

### API Documentation
- Interactive Swagger UI: https://localhost:8000/docs
- OpenAPI JSON: https://localhost:8000/openapi.json

### Additional Resources
- [YOLO11 Documentation](https://docs.ultralytics.com/)
- [BitNet Repository](https://github.com/microsoft/BitNet)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Firebase Documentation](https://firebase.google.com/docs)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

---

## 🤝 Contributing

This is a coursework project. For questions or issues, please contact the course instructor.

---

## 📄 License

This project is submitted as coursework for 5CCSACCA Cloud Computing for Artificial Intelligence at King's College London.

---

## 👤 Author

**Armita Eslami**  
King's College London  
Course: 5CCSACCA Cloud Computing for Artificial Intelligence

---

## 🙏 Acknowledgments

- King's College London Computer Science Department
- Course Instructor: Dr. Héctor Menéndez
- Ultralytics for YOLO11
- Microsoft Research for BitNet
- FastAPI, Firebase, and Prometheus communities

---

## 📝 Notes

### Development vs Production

**This project is configured for development/demonstration.**

For production deployment:
1. Replace self-signed certificates with CA-signed certificates
2. Configure proper CORS origins
3. Use managed database services (MongoDB Atlas, Firebase)
4. Implement proper secret management (AWS Secrets Manager, etc.)
5. Set up CI/CD pipelines
6. Configure auto-scaling
7. Implement comprehensive logging
8. Set up backup and disaster recovery

### Performance Considerations

- BitNet LLM requires **8GB+ RAM**
- YOLO inference takes **~0.5-2 seconds** per image
- LLM generation takes **~3-10 seconds** depending on complexity
- RabbitMQ queue helps handle burst traffic
- Consider GPU acceleration for production workloads

---

**Last Updated:** December 21, 2025  
**Version:** 1.0.0  
**Status:** ✅ All 11 Stages Complete