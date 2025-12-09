"""
Configuration management for API Gateway
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # MongoDB
    mongodb_uri: str = "mongodb://mongodb:27017/"
    mongodb_database: str = "mydatabase"
    
    # RabbitMQ
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_queue: str = "detection_queue"
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    
    # Service URLs
    yolo_service_url: str = "http://yolo-service:8001"
    llm_service_url: str = "http://llm-service:8002"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    
    # Firebase
    firebase_key_path: str = "/app/firebase_key.json"
    
    # Security
    secret_key: str = "change-me-in-production"
    allowed_origins: str = "*"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
