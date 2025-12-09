"""
Postprocessor Service

Consumes messages from RabbitMQ and performs post-processing on detection results.
Stores enriched data in MongoDB.
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any

import pika
from pika.exceptions import AMQPConnectionError
from pymongo import MongoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "detection_queue")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "mydatabase")


class PostprocessorService:
    """
    Post-processing service that enriches detection data.
    
    This service:
    1. Consumes messages from RabbitMQ
    2. Adds computed fields (total objects, categories, etc.)
    3. Stores enriched data in MongoDB
    """
    
    def __init__(self):
        self.mongo_client = None
        self.db = None
        self.collection = None
        
    def connect_mongodb(self):
        """Establish MongoDB connection"""
        try:
            self.mongo_client = MongoClient(MONGODB_URI)
            self.db = self.mongo_client[MONGODB_DATABASE]
            self.collection = self.db["postprocessed"]
            
            # Test connection
            self.mongo_client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def postprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich detection data with computed fields.
        
        Args:
            data: Original detection data
        
        Returns:
            Enriched data dictionary
        """
        objects = data.get("objects", {})
        
        # Compute statistics
        total_objects = sum(objects.values())
        unique_classes = len(objects)
        
        # Categorize objects
        categories = self._categorize_objects(objects)
        
        # Add confidence summary if available
        confidence_scores = data.get("confidence_scores", {})
        avg_confidence = self._calculate_avg_confidence(confidence_scores)
        
        # Enriched data
        enriched = {
            **data,
            "postprocessed": True,
            "postprocessed_at": datetime.utcnow().isoformat(),
            "statistics": {
                "total_objects": total_objects,
                "unique_classes": unique_classes,
                "categories": categories,
                "average_confidence": avg_confidence
            }
        }
        
        return enriched
    
    def _categorize_objects(self, objects: Dict[str, int]) -> Dict[str, list]:
        """Categorize detected objects into groups"""
        # COCO dataset categories mapping
        categories = {
            "people": ["person"],
            "vehicles": ["car", "truck", "bus", "motorcycle", "bicycle", "airplane", "boat", "train"],
            "animals": ["dog", "cat", "bird", "horse", "cow", "sheep", "elephant", "bear", "zebra", "giraffe"],
            "furniture": ["chair", "couch", "bed", "dining table", "toilet"],
            "electronics": ["tv", "laptop", "cell phone", "keyboard", "mouse", "remote"],
            "food": ["banana", "apple", "orange", "sandwich", "pizza", "donut", "cake", "carrot", "hot dog"],
            "sports": ["sports ball", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "frisbee", "skis", "snowboard", "kite"],
            "kitchen": ["bottle", "cup", "fork", "knife", "spoon", "bowl", "wine glass"],
            "other": []
        }
        
        result = {cat: [] for cat in categories}
        
        for obj_name, count in objects.items():
            categorized = False
            for category, items in categories.items():
                if obj_name.lower() in [i.lower() for i in items]:
                    result[category].append({"name": obj_name, "count": count})
                    categorized = True
                    break
            
            if not categorized:
                result["other"].append({"name": obj_name, "count": count})
        
        # Remove empty categories
        return {k: v for k, v in result.items() if v}
    
    def _calculate_avg_confidence(self, confidence_scores: Dict[str, list]) -> float:
        """Calculate average confidence across all detections"""
        if not confidence_scores:
            return 0.0
        
        all_scores = []
        for scores in confidence_scores.values():
            all_scores.extend(scores)
        
        if not all_scores:
            return 0.0
        
        return round(sum(all_scores) / len(all_scores), 4)
    
    def save_postprocessed(self, data: Dict[str, Any]) -> str:
        """
        Save postprocessed data to MongoDB.
        
        Args:
            data: Enriched detection data
        
        Returns:
            Document ID
        """
        data["timestamp"] = datetime.utcnow()
        result = self.collection.insert_one(data)
        return str(result.inserted_id)
    
    def process_message(self, body: bytes):
        """
        Process a single message from RabbitMQ.
        
        Args:
            body: Raw message body
        """
        try:
            data = json.loads(body.decode("utf-8"))
            logger.info(f"Processing message: {data.get('type', 'unknown')}")
            
            # Postprocess the data
            enriched_data = self.postprocess_data(data)
            
            # Save to MongoDB
            doc_id = self.save_postprocessed(enriched_data)
            logger.info(f"Saved postprocessed data with ID: {doc_id}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise
    
    def start_consuming(self):
        """Start consuming messages from RabbitMQ"""
        # Connect to MongoDB first
        self.connect_mongodb()
        
        # Connection parameters for RabbitMQ
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        while True:
            try:
                logger.info(f"Connecting to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
                connection = pika.BlockingConnection(parameters)
                channel = connection.channel()
                
                # Declare queue
                channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
                
                # Set QoS
                channel.basic_qos(prefetch_count=1)
                
                logger.info(f"Waiting for messages on queue: {RABBITMQ_QUEUE}")
                
                def callback(ch, method, properties, body):
                    """Message callback handler"""
                    try:
                        self.process_message(body)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
                        # Negative acknowledgment - requeue the message
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                
                channel.basic_consume(
                    queue=RABBITMQ_QUEUE,
                    on_message_callback=callback
                )
                
                channel.start_consuming()
                
            except AMQPConnectionError as e:
                logger.warning(f"RabbitMQ connection error: {e}")
                logger.info("Retrying in 5 seconds...")
                time.sleep(5)
            except KeyboardInterrupt:
                logger.info("Received interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.info("Retrying in 5 seconds...")
                time.sleep(5)
        
        # Cleanup
        if self.mongo_client:
            self.mongo_client.close()


def main():
    """Main entry point"""
    logger.info("Starting Postprocessor Service...")
    
    service = PostprocessorService()
    service.start_consuming()


if __name__ == "__main__":
    main()
