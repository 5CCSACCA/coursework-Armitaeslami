"""
RabbitMQ Service for Message Queue

Handles publishing messages to RabbitMQ for async processing.
"""

import json
import logging
from typing import Dict, Any, Optional

import pika
from pika.exceptions import AMQPConnectionError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RabbitMQService:
    """RabbitMQ message queue service"""
    
    def __init__(self):
        self._connection = None
        self._channel = None
    
    def _get_connection_params(self) -> pika.ConnectionParameters:
        """Get RabbitMQ connection parameters"""
        credentials = pika.PlainCredentials(
            settings.rabbitmq_user,
            settings.rabbitmq_password
        )
        
        return pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
    
    def _get_channel(self):
        """Get or create RabbitMQ channel"""
        try:
            if self._connection is None or self._connection.is_closed:
                self._connection = pika.BlockingConnection(
                    self._get_connection_params()
                )
                self._channel = self._connection.channel()
                
                # Declare the queue
                self._channel.queue_declare(
                    queue=settings.rabbitmq_queue,
                    durable=True
                )
                
                logger.info("Connected to RabbitMQ")
            
            return self._channel
            
        except AMQPConnectionError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def publish_message(
        self,
        message: Dict[str, Any],
        routing_key: Optional[str] = None
    ) -> bool:
        """
        Publish a message to RabbitMQ.
        
        Args:
            message: Dictionary to publish as JSON
            routing_key: Optional routing key (defaults to queue name)
        
        Returns:
            True if published successfully, False otherwise
        """
        try:
            channel = self._get_channel()
            
            body = json.dumps(message)
            queue = routing_key or settings.rabbitmq_queue
            
            channel.basic_publish(
                exchange="",
                routing_key=queue,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type="application/json"
                )
            )
            
            logger.info(f"Published message to queue: {queue}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing to RabbitMQ: {e}")
            self._connection = None
            self._channel = None
            return False
    
    def publish_detection(
        self,
        objects: Dict[str, int],
        description: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Publish a detection result for post-processing.
        
        Args:
            objects: Detected objects dictionary
            description: Generated description
            user_id: Optional user ID
            metadata: Optional additional metadata
        
        Returns:
            True if published successfully
        """
        message = {
            "type": "detection",
            "objects": objects,
            "description": description,
            "user_id": user_id,
            "metadata": metadata or {}
        }
        
        return self.publish_message(message)
    
    def close(self):
        """Close RabbitMQ connection"""
        try:
            if self._connection and not self._connection.is_closed:
                self._connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
        finally:
            self._connection = None
            self._channel = None
    
    def health_check(self) -> bool:
        """
        Check if RabbitMQ connection is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            channel = self._get_channel()
            return channel is not None and channel.is_open
        except Exception:
            return False


# Global instance
rabbitmq_service = RabbitMQService()


def get_rabbitmq_service() -> RabbitMQService:
    """Dependency for getting RabbitMQ service"""
    return rabbitmq_service


def publish_detection_to_rabbitmq(detection_data: Dict[str, Any]) -> bool:
    """
    Convenience function to publish detection data.
    
    Args:
        detection_data: Detection result dictionary
    
    Returns:
        True if published successfully
    """
    return rabbitmq_service.publish_message(detection_data)
