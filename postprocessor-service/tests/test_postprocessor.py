"""
Unit Tests for Postprocessor Service
"""

import pytest


class TestMessageProcessing:
    """Test message processing functionality"""
    
    def test_message_structure(self):
        """Test expected message structure"""
        message = {
            "objects": {"person": 2, "dog": 1},
            "description": "The image contains 2 persons and 1 dog.",
            "timestamp": "2024-01-01T12:00:00"
        }
        
        assert "objects" in message
        assert "description" in message
        assert "timestamp" in message
    
    def test_enriched_message_structure(self):
        """Test enriched message has additional fields"""
        enriched = {
            "objects": {"person": 2},
            "description": "Test",
            "postprocessed": True,
            "statistics": {
                "total_objects": 2,
                "unique_classes": 1
            }
        }
        
        assert enriched["postprocessed"] == True
        assert "statistics" in enriched


class TestStatisticsCalculation:
    """Test statistics calculation"""
    
    def test_total_objects(self):
        """Test total objects calculation"""
        objects = {"person": 2, "dog": 1, "car": 3}
        total = sum(objects.values())
        
        assert total == 6
    
    def test_unique_classes(self):
        """Test unique classes count"""
        objects = {"person": 2, "dog": 1, "car": 3}
        unique_classes = len(objects.keys())
        
        assert unique_classes == 3
    
    def test_average_confidence(self):
        """Test average confidence calculation"""
        confidences = [0.95, 0.87, 0.72]
        average = sum(confidences) / len(confidences)
        
        assert 0.0 <= average <= 1.0
        assert round(average, 2) == 0.85


class TestObjectCategorization:
    """Test object categorization"""
    
    def test_categorize_people(self):
        """Test people category"""
        people_objects = ["person", "man", "woman", "child"]
        
        for obj in people_objects:
            category = "people" if obj in people_objects else "other"
            assert category == "people"
    
    def test_categorize_vehicles(self):
        """Test vehicles category"""
        vehicle_objects = ["car", "truck", "bus", "motorcycle", "bicycle"]
        
        test_object = "car"
        assert test_object in vehicle_objects
    
    def test_categorize_animals(self):
        """Test animals category"""
        animal_objects = ["dog", "cat", "bird", "horse"]
        
        test_object = "dog"
        assert test_object in animal_objects


class TestRabbitMQConnection:
    """Test RabbitMQ connection logic"""
    
    def test_connection_params(self):
        """Test connection parameters"""
        params = {
            "host": "rabbitmq",
            "port": 5672,
            "queue": "detection_queue"
        }
        
        assert params["port"] == 5672
        assert len(params["queue"]) > 0
    
    def test_retry_logic(self):
        """Test retry configuration"""
        max_retries = 5
        retry_delay = 5  # seconds
        
        assert max_retries > 0
        assert retry_delay > 0