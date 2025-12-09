"""YOLO Object Detection Service"""

import os
import io
import logging
from typing import Dict, List, Any
from collections import Counter

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
from ultralytics import YOLO
from prometheus_client import Counter as PromCounter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
DETECTION_REQUESTS = PromCounter(
    'yolo_detection_requests_total',
    'Total number of detection requests'
)
DETECTION_LATENCY = Histogram(
    'yolo_detection_latency_seconds',
    'Time spent processing detection requests'
)
OBJECTS_DETECTED = PromCounter(
    'yolo_objects_detected_total',
    'Total number of objects detected',
    ['class_name']
)

# Initialize FastAPI app
app = FastAPI(
    title="YOLO Object Detection Service",
    description="Microservice for object detection using YOLOv11n",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response models
class DetectionResult(BaseModel):
    """Model for detection results"""
    objects: Dict[str, int]
    confidence_scores: Dict[str, List[float]]
    total_objects: int

class HealthResponse(BaseModel):
    """Model for health check response"""
    status: str
    service: str
    model_loaded: bool


# Global model instance
model = None


def get_model() -> YOLO:
    """Lazy load the YOLO model"""
    global model
    if model is None:
        model_path = os.getenv("MODEL_PATH", "yolo11n.pt")
        logger.info(f"Loading YOLO model from {model_path}")
        model = YOLO(model_path)
        logger.info("YOLO model loaded successfully")
    return model


@app.on_event("startup")
async def startup_event():
    logger.info("Starting YOLO service...")
    get_model()
    logger.info("YOLO service started successfully")


@app.get("/", response_model=Dict[str, str])
async def root():
    return {"message": "YOLO Object Detection Service is running"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="yolo-service",
        model_loaded=model is not None
    )


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/detect", response_model=DetectionResult)
async def detect_objects(file: UploadFile = File(...)):
    
    DETECTION_REQUESTS.inc()
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image (JPEG, PNG, etc.)"
        )
    
    try:
        with DETECTION_LATENCY.time():
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            
            # Convert to RGB 
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get model and run detection
            yolo_model = get_model()
            results = yolo_model(image)
            
            # Process results
            detected_objects: Dict[str, int] = {}
            confidence_scores: Dict[str, List[float]] = {}
            
            if len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                class_ids = boxes.cls.tolist()
                confidences = boxes.conf.tolist()
                
                for class_id, confidence in zip(class_ids, confidences):
                    class_name = results[0].names[int(class_id)]
                    
                    # Count objects
                    detected_objects[class_name] = detected_objects.get(class_name, 0) + 1
                    
                    # Store confidence scores
                    if class_name not in confidence_scores:
                        confidence_scores[class_name] = []
                    confidence_scores[class_name].append(round(confidence, 4))
                    
                    # Update metrics
                    OBJECTS_DETECTED.labels(class_name=class_name).inc()
            
            total_objects = sum(detected_objects.values())
            
            logger.info(f"Detected {total_objects} objects in image")
            
            return DetectionResult(
                objects=detected_objects,
                confidence_scores=confidence_scores,
                total_objects=total_objects
            )
            
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )


@app.post("/detect/batch")
async def detect_objects_batch(files: List[UploadFile] = File(...)):
    
    results = []
    for file in files:
        result = await detect_objects(file)
        results.append(result)
    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
