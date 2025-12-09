# Cloud Computing for Artificial Intelligence – armita

This project implements a small cloud-based AI system made up of several services.  
The system exposes a YOLO model for image analysis, an LLM service for text processing, and a post-processing service connected through RabbitMQ.  
Everything runs together using Docker Compose.

---

## How to Run

### Build
docker compose build

### Start
docker compose up

### Run tests
./scripts/test.sh
(or test.bat on Windows)

---

## Stages Overview

### Stage 1 – Initial Model Setup
I created the YOLO service and wrote basic code to load the model and run inference on images.  
The LLM service was also set up with a simple text endpoint.  
This stage was mainly about getting both models working before exposing them.

### Stage 2 – Containerisation
Each service received its own Dockerfile.  
I tested the images individually to make sure the models and FastAPI apps ran correctly inside containers.

### Stage 3 – API Exposure
I added FastAPI endpoints for YOLO and the LLM.  
The API gateway was introduced to act as a single entry point, forwarding requests to each service.

### Stage 4 – Database and History
A small database layer was added to the gateway.  
Each request is recorded with its details, and a `/history` endpoint returns past interactions.

### Stage 5 – Firebase Storage
Firebase storage was integrated to save outputs externally.  
I added endpoints for retrieving, updating, and deleting stored results.  
The firebase_key.json file is used locally, with configuration handled through environment variables.

### Stage 6 – Post-Processing + RabbitMQ
A second service was created for processing outputs from YOLO.  
The gateway sends messages to RabbitMQ, and the post-processing service receives them and performs its task.  
Docker Compose runs all services together.

### Stage 7 – Authentication
Firebase authentication was added to secure the API.  
Protected routes now require a valid Bearer token, and the user ID from the token is stored with database entries.

### Stage 8 – Cost Estimation
I calculated estimated infrastructure costs using the assumptions in the specification.  
A short explanation is included in pricing.md.

### Stage 9 – Monitoring
Prometheus and Grafana were added under the monitoring folder.  
Prometheus collects metrics, and Grafana provides a dashboard for visualising them.

### Stage 10 – Testing
Each service includes unit tests in its tests folder.  
The test scripts run all tests together.

### Stage 11 – Security
Security improvements were added throughout the system:
- token authentication is enforced,
- database entries are tied to the authenticated user,
- Firebase rules protect stored data,
- sensitive keys are stored in environment variables.

I tested the secured endpoints using curl to confirm correct behaviour.

---

## Project Structure

.
├── api-gateway/           # Main public API
├── yolo-service/          # YOLO inference service
├── llm-service/           # LLM service
├── postprocessor-service/ # RabbitMQ post-processing service
├── monitoring/            # Prometheus + Grafana
├── scripts/               # Build/run/test tools
├── docker-compose.yml
├── firebase_key.json
├── pricing.md
└── README.md

---

## Example Requests

### YOLO Prediction
curl -X POST http://localhost:8000/predict/yolo \
     -H "Authorization: Bearer <TOKEN>" \
     -F "file=@image.jpg"

### View History
curl http://localhost:8000/history \
     -H "Authorization: Bearer <TOKEN>"

---

## Notes
- GitFlow was used for development.
- The final working version is merged into the main branch.
- The system is designed to run within the required hardware limits.
