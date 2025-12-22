"""
API Gateway - Main Entry Point

Central API gateway that orchestrates YOLO detection, LLM processing,
database persistence, Firebase storage, and message queue publishing.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import Counter as PromCounter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
import requests

from app.config import get_settings
from app.auth import get_current_user, get_authenticated_user, AuthenticatedUser
from app.db_service import get_db_service, DatabaseService
from app.firebase_service import get_firebase_service, FirebaseService
from app.rabbitmq_service import get_rabbitmq_service, RabbitMQService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Settings
settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Prometheus metrics
REQUEST_COUNT = PromCounter(
    'api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status']
)
REQUEST_LATENCY = Histogram(
    'api_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint']
)

# Initialize FastAPI app
app = FastAPI(
    title="Cloud AI SaaS API",
    description="API Gateway for YOLO Object Detection and BitNet LLM Services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter to app state
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return Response(
        content='{"detail": "Rate limit exceeded"}',
        status_code=429,
        media_type="application/json"
    )


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000)
    max_tokens: int = Field(default=100, ge=1, le=512)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class FirebaseUpdateRequest(BaseModel):
    objects: Optional[Dict[str, int]] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    services: Dict[str, bool]


# HTTP client for internal services
http_client = httpx.AsyncClient(timeout=60.0)


async def call_yolo_service(image_data: bytes) -> Dict[str, Any]:
    """Call YOLO service for object detection"""
    try:
        files = {"file": ("image.jpg", image_data, "image/jpeg")}
        response = await http_client.post(
            f"{settings.yolo_service_url}/detect",
            files=files
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"YOLO service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YOLO detection service unavailable"
        )


async def call_llm_service(objects: Dict[str, int], style: str = "descriptive") -> Dict[str, Any]:
    """Call LLM service for description generation"""
    try:
        response = await http_client.post(
            f"{settings.llm_service_url}/describe",
            json={"objects": objects, "style": style}
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"LLM service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable"
        )


async def call_llm_generate(prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
    """Call LLM service for text generation"""
    try:
        response = await http_client.post(
            f"{settings.llm_service_url}/generate",
            json={"prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"LLM generate error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable"
        )


# ============================================
# Public Endpoints (No Auth Required)
# ============================================

@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {"message": "Cloud AI SaaS API is running", "version": "1.0.0"}


@app.get("/health", response_model=HealthResponse)
async def health_check(
    db: DatabaseService = Depends(get_db_service),
    firebase: FirebaseService = Depends(get_firebase_service),
    rabbitmq: RabbitMQService = Depends(get_rabbitmq_service)
):
    """Health check for all services"""
    services = {
        "api_gateway": True,
        "mongodb": db.health_check(),
        "firebase": firebase.health_check(),
        "rabbitmq": rabbitmq.health_check()
    }
    
    # Check YOLO service
    try:
        resp = await http_client.get(f"{settings.yolo_service_url}/health", timeout=5.0)
        services["yolo_service"] = resp.status_code == 200
    except Exception:
        services["yolo_service"] = False
    
    # Check LLM service
    try:
        resp = await http_client.get(f"{settings.llm_service_url}/health", timeout=5.0)
        services["llm_service"] = resp.status_code == 200
    except Exception:
        services["llm_service"] = False
    
    all_healthy = all(services.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        services=services
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/detect")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def detect_objects(
    request: Request,
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_authenticated_user),
    db: DatabaseService = Depends(get_db_service),
    rabbitmq: RabbitMQService = Depends(get_rabbitmq_service)
):
    """
    Detect objects in an uploaded image using YOLO.
    Publishes to RabbitMQ for post-processing (story generation).
    
    Requires authentication via Firebase ID token.
    """
    REQUEST_COUNT.labels(endpoint="/detect", method="POST", status="started").inc()
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    with REQUEST_LATENCY.labels(endpoint="/detect").time():
        # Step 1: YOLO detection
        image_data = await file.read()
        result = await call_yolo_service(image_data)
        
        # Extract detection data
        objects = result.get("objects", {})
        description = result.get("description", "")
        confidence_scores = result.get("confidence_scores", {})
        
        # Step 2: Save to MongoDB
        db.save_record(objects, description, user_id=user.uid)
        
        # Step 3: Publish to RabbitMQ for post-processing (story generation)
        try:
            rabbitmq.publish_detection(
                objects=objects,
                description=description,
                user_id=user.uid,
                metadata={"confidence_scores": confidence_scores}
            )
            logger.info(f"Published detection to RabbitMQ for user {user.uid}")
        except Exception as e:
            logger.error(f"Failed to publish to RabbitMQ: {e}")
            # Don't fail the request if RabbitMQ is down
    
    REQUEST_COUNT.labels(endpoint="/detect", method="POST", status="success").inc()
    
    return {
        **result,
        "message": "Detection complete. Processing story generation in background."
    }


@app.post("/generate")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def generate_text(
    request: Request,
    body: GenerateRequest,
    user: dict = Depends(get_current_user)
):
    """
    Generate text using BitNet LLM.
    
    Requires authentication via Firebase ID token.
    """
    REQUEST_COUNT.labels(endpoint="/generate", method="POST", status="started").inc()
    
    with REQUEST_LATENCY.labels(endpoint="/generate").time():
        result = await call_llm_generate(body.prompt, body.max_tokens, body.temperature)
    
    REQUEST_COUNT.labels(endpoint="/generate", method="POST", status="success").inc()
    return result


@app.post("/describe")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def describe_image(
    request: Request,
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_authenticated_user),
    db: DatabaseService = Depends(get_db_service),
    firebase: FirebaseService = Depends(get_firebase_service),
    rabbitmq: RabbitMQService = Depends(get_rabbitmq_service)
):
    """
    Full pipeline: Detect objects, generate description, save to DB and Firebase,
    and publish to RabbitMQ for post-processing.
    
    Requires authentication via Firebase ID token.
    """
    REQUEST_COUNT.labels(endpoint="/describe", method="POST", status="started").inc()
    
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    with REQUEST_LATENCY.labels(endpoint="/describe").time():
        # Step 1: YOLO detection
        image_data = await file.read()
        detection_result = await call_yolo_service(image_data)
        objects = detection_result.get("objects", {})
        
        # Step 2: LLM description
        llm_result = await call_llm_service(objects)
        description = llm_result.get("description", "")
        
        # Step 3: Save to MongoDB
        db.save_record(objects, description, user_id=user.uid)
        
        # Step 4: Save to Firebase
        firebase.save_record(objects, description, user_id=user.uid)
        
        # Step 5: Publish to RabbitMQ
        rabbitmq.publish_detection(objects, description, user_id=user.uid)
    
    REQUEST_COUNT.labels(endpoint="/describe", method="POST", status="success").inc()
    
    return {
        "objects": objects,
        "description": description,
        "message": "Sent to RabbitMQ for post-processing"
    }


@app.get("/history")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_history(
    request: Request,
    limit: int = 100,
    skip: int = 0,
    user: AuthenticatedUser = Depends(get_authenticated_user),
    db: DatabaseService = Depends(get_db_service)
):
    """
    Get detection history from MongoDB.
    
    Requires authentication via Firebase ID token.
    """
    records = db.get_all_records(user_id=user.uid, limit=limit, skip=skip)
    return {"history": records, "count": len(records)}


@app.get("/history/stats")
async def get_history_stats(
    user: AuthenticatedUser = Depends(get_authenticated_user),
    db: DatabaseService = Depends(get_db_service)
):
    """Get database statistics"""
    return db.get_stats()




@app.get("/firebase/history")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def firebase_history(
    request: Request,
    limit: int = 100,
    user: AuthenticatedUser = Depends(get_authenticated_user),
    firebase: FirebaseService = Depends(get_firebase_service)
):
    """Get all records from Firebase Firestore"""
    records = firebase.get_all(user_id=user.uid, limit=limit)
    return {"records": records, "count": len(records)}


@app.get("/firebase/{doc_id}")
async def get_firebase_record(
    doc_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
    firebase: FirebaseService = Depends(get_firebase_service)
):
    """Get a specific record from Firebase"""
    record = firebase.get_record(doc_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@app.put("/firebase/update/{doc_id}")
async def update_firebase_record(
    doc_id: str,
    data: FirebaseUpdateRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
    firebase: FirebaseService = Depends(get_firebase_service)
):
    """Update a record in Firebase"""
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    success = firebase.update_record(doc_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update record")
    
    return {"message": "Updated successfully", "doc_id": doc_id}


@app.delete("/firebase/delete/{doc_id}")
async def delete_firebase_record(
    doc_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
    firebase: FirebaseService = Depends(get_firebase_service)
):
    """Delete a record from Firebase"""
    success = firebase.delete_record(doc_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete record")
    
    return {"message": "Deleted successfully", "doc_id": doc_id}

@app.get("/postprocessed")
async def get_postprocessed(
    limit: int = 100,
    skip: int = 0,
    user: AuthenticatedUser = Depends(get_authenticated_user),
    db: DatabaseService = Depends(get_db_service)
):
    """Get postprocessed results from MongoDB"""
    records = db.get_postprocessed_records(limit=limit, skip=skip)
    return {"records": records, "count": len(records)}

@app.get("/stories")
def get_stories(
    limit: int = 10,
    skip: int = 0,
    user: AuthenticatedUser = Depends(get_authenticated_user),
    db: DatabaseService = Depends(get_db_service),
):
    records = db.get_postprocessed_records(limit=limit, skip=skip)
    return {"records": records, "count": len(records)}




@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting API Gateway...")
    logger.info(f"YOLO Service URL: {settings.yolo_service_url}")
    logger.info(f"LLM Service URL: {settings.llm_service_url}")
    logger.info("API Gateway started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down API Gateway...")
    await http_client.aclose()
    logger.info("API Gateway shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
