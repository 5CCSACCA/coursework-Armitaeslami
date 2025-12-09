"""
LLM Service - BitNet Language Model

This microservice provides text generation using Microsoft's BitNet.cpp
following the official BitNet inference framework.

Reference: https://github.com/microsoft/BitNet
"""

import os
import logging
import subprocess
import tempfile
from typing import Dict, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter as PromCounter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
GENERATION_REQUESTS = PromCounter(
    'llm_generation_requests_total',
    'Total number of text generation requests'
)
GENERATION_LATENCY = Histogram(
    'llm_generation_latency_seconds',
    'Time spent generating text'
)
TOKENS_GENERATED = PromCounter(
    'llm_tokens_generated_total',
    'Total number of tokens generated'
)

# Initialize FastAPI app
app = FastAPI(
    title="LLM Service - BitNet",
    description="Microservice for text generation using BitNet/1-bit LLM",
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

# BitNet configuration
BITNET_PATH = Path(os.getenv("BITNET_PATH", "/app/BitNet"))
BITNET_MODEL_PATH = Path(os.getenv("BITNET_MODEL_PATH", 
                                    "/app/BitNet/models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf"))
BITNET_BINARY = BITNET_PATH / "build" / "bin" / "llama-cli"


# Request/Response models
class GenerateRequest(BaseModel):
    """Request model for text generation"""
    prompt: str = Field(..., description="Input prompt", min_length=1, max_length=1000)
    max_tokens: int = Field(default=100, ge=1, le=512, description="Maximum tokens")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Describe what you see in an image with a dog and two people",
                "max_tokens": 100,
                "temperature": 0.7
            }
        }


class DescribeRequest(BaseModel):
    """Request model for describing detected objects"""
    objects: Dict[str, int] = Field(..., description="Object counts")
    style: str = Field(default="descriptive", description="Style: descriptive, brief, detailed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "objects": {"person": 2, "dog": 1, "car": 3},
                "style": "descriptive"
            }
        }


class GenerateResponse(BaseModel):
    """Response model for text generation"""
    prompt: str
    response: str
    tokens_generated: int
    model: str


class DescribeResponse(BaseModel):
    """Response model for object description"""
    objects: Dict[str, int]
    description: str
    model: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    model_loaded: bool
    model_path: str
    bitnet_available: bool


class BitNetInference:
    """Wrapper for BitNet.cpp inference"""
    
    def __init__(self):
        self.model_path = BITNET_MODEL_PATH
        self.binary_path = BITNET_BINARY
        self.run_inference_script = BITNET_PATH / "run_inference.py"
        self.is_available = self._check_availability()
        
    def _check_availability(self) -> bool:
        """Check if BitNet is properly set up"""
        checks = {
            "Model file": self.model_path.exists(),
            "BitNet binary": self.binary_path.exists(),
            "Run script": self.run_inference_script.exists(),
        }
        
        for name, status in checks.items():
            logger.info(f"{name}: {'✓' if status else '✗'}")
        
        return all(checks.values())
    
    def generate(self, prompt: str, max_tokens: int = 100, 
                 temperature: float = 0.7) -> tuple[str, int]:
        """
        Generate text using BitNet.cpp
        
        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Tuple of (generated_text, token_count)
        """
        if not self.is_available:
            raise RuntimeError("BitNet not properly configured")
        
        try:
            # Use the run_inference.py script following BitNet documentation
            cmd = [
                "python",
                str(self.run_inference_script),
                "-m", str(self.model_path),
                "-p", prompt,
                "-n", str(max_tokens),
                "-t", "2",  # threads
                "-temp", str(temperature),
                "-c", "512"  # context size
            ]
            
            logger.info(f"Running BitNet inference with prompt: {prompt[:50]}...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(BITNET_PATH)
            )
            
            if result.returncode != 0:
                logger.error(f"BitNet error: {result.stderr}")
                raise RuntimeError(f"BitNet inference failed: {result.stderr}")
            
            # Parse output
            output = result.stdout.strip()
            
            # The output contains the full conversation including the prompt
            # Extract just the generated part
            if prompt in output:
                generated = output.split(prompt, 1)[1].strip()
            else:
                generated = output
            
            # Estimate token count (rough approximation: 4 chars per token)
            token_count = len(generated) // 4
            
            logger.info(f"Generated {token_count} tokens")
            
            return generated, token_count
            
        except subprocess.TimeoutExpired:
            logger.error("BitNet inference timed out")
            raise RuntimeError("Generation timed out")
        except Exception as e:
            logger.error(f"BitNet generation error: {e}")
            raise
    
    def describe_objects(self, objects: Dict[str, int], style: str = "descriptive") -> str:
        """
        Generate description of detected objects
        
        Args:
            objects: Dictionary of object names and counts
            style: Description style
            
        Returns:
            Natural language description
        """
        if not objects:
            return "No objects were detected in the image."
        
        # Build object list
        parts = []
        for obj_name, count in objects.items():
            if count == 1:
                parts.append(f"1 {obj_name}")
            else:
                plural = obj_name + "s" if not obj_name.endswith("s") else obj_name
                parts.append(f"{count} {plural}")
        
        if style == "brief":
            return f"Detected: {', '.join(parts)}."
        
        elif style == "detailed":
            # Use BitNet to generate a more detailed description
            prompt = f"Write a detailed description of an image containing: {', '.join(parts)}. Describe the scene in 2-3 sentences."
            try:
                description, _ = self.generate(prompt, max_tokens=150, temperature=0.7)
                return description
            except Exception as e:
                logger.warning(f"BitNet generation failed, using fallback: {e}")
                # Fallback to simple description
                total = sum(objects.values())
                obj_list = ", ".join(parts[:-1]) + f", and {parts[-1]}" if len(parts) > 1 else parts[0]
                return (
                    f"The image analysis detected a total of {total} objects. "
                    f"Specifically, the following were identified: {obj_list}. "
                    f"These objects together compose the main elements visible in the scene."
                )
        
        else:  # descriptive (default)
            if len(parts) == 1:
                return f"The image contains {parts[0]}."
            elif len(parts) == 2:
                return f"The image contains {parts[0]} and {parts[1]}."
            else:
                return f"The image contains {', '.join(parts[:-1])}, and {parts[-1]}."


# Global BitNet instance
bitnet = BitNetInference()


@app.on_event("startup")
async def startup_event():
    """Verify BitNet on startup"""
    logger.info("Starting LLM service...")
    logger.info(f"BitNet path: {BITNET_PATH}")
    logger.info(f"Model path: {BITNET_MODEL_PATH}")
    logger.info(f"Binary path: {BITNET_BINARY}")
    
    if bitnet.is_available:
        logger.info("✓ BitNet is ready")
    else:
        logger.error("✗ BitNet is not properly configured")
        logger.error("Make sure the model was downloaded and compiled during build")
    
    logger.info("LLM service started")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {"message": "LLM Service (BitNet) is running"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if bitnet.is_available else "degraded",
        service="llm-service",
        model_loaded=bitnet.model_path.exists(),
        model_path=str(bitnet.model_path),
        bitnet_available=bitnet.is_available
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """
    Generate text from a prompt using BitNet LLM.
    
    This uses the actual BitNet.cpp inference engine.
    """
    GENERATION_REQUESTS.inc()
    
    if not bitnet.is_available:
        raise HTTPException(
            status_code=503,
            detail="BitNet service not available. Check model and binary."
        )
    
    try:
        with GENERATION_LATENCY.time():
            response_text, token_count = bitnet.generate(
                prompt=request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            TOKENS_GENERATED.inc(token_count)
            
            return GenerateResponse(
                prompt=request.prompt,
                response=response_text,
                tokens_generated=token_count,
                model="BitNet-b1.58-2B-4T"
            )
            
    except Exception as e:
        logger.error(f"Error generating text: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating text: {str(e)}"
        )


@app.post("/describe", response_model=DescribeResponse)
async def describe_objects(request: DescribeRequest):
    """
    Generate a natural language description of detected objects.
    """
    GENERATION_REQUESTS.inc()
    
    try:
        description = bitnet.describe_objects(
            objects=request.objects,
            style=request.style
        )
        
        return DescribeResponse(
            objects=request.objects,
            description=description,
            model="BitNet-b1.58-2B-4T"
        )
        
    except Exception as e:
        logger.error(f"Error describing objects: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error describing objects: {str(e)}"
        )


@app.get("/models")
async def list_models():
    """List model information"""
    return {
        "model": "BitNet-b1.58-2B-4T",
        "quantization": "i2_s",
        "model_path": str(bitnet.model_path),
        "is_available": bitnet.is_available,
        "description": "1-bit quantized LLM from Microsoft Research"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)