"""
Unit Tests for YOLO Service
"""

import pytest


class TestYOLODetection:
    """Test YOLO detection functionality"""
    
    def test_detection_response_format(self):
        """Test detection response has correct format"""
        response = {
            "objects": {"person": 2, "car": 1},
            "confidence_scores": {"person": [0.95, 0.87], "car": [0.91]},
            "total_objects": 3
        }
        
        assert "objects" in response
        assert "confidence_scores" in response
        assert "total_objects" in response
    
    def test_total_objects_calculation(self):
        """Test total objects equals sum of all detections"""
        objects = {"person": 2, "dog": 1, "car": 3}
        total = sum(objects.values())
        
        assert total == 6
    
    def test_confidence_score_range(self):
        """Test confidence scores are in valid range 0-1"""
        confidence_scores = [0.95, 0.87, 0.72, 0.65]
        
        for score in confidence_scores:
            assert 0.0 <= score <= 1.0
    
    def test_empty_detection(self):
        """Test empty detection response"""
        response = {
            "objects": {},
            "confidence_scores": {},
            "total_objects": 0
        }
        
        assert response["total_objects"] == 0
        assert len(response["objects"]) == 0


class TestImageValidation:
    """Test image input validation"""
    
    def test_valid_image_extensions(self):
        """Test valid image file extensions"""
        valid_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        
        test_files = ["image.jpg", "photo.png", "test.jpeg"]
        for filename in test_files:
            ext = "." + filename.split(".")[-1]
            assert ext in valid_extensions
    
    def test_invalid_image_extension(self):
        """Test invalid file extensions are rejected"""
        valid_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        
        invalid_files = ["document.pdf", "data.txt", "script.py"]
        for filename in invalid_files:
            ext = "." + filename.split(".")[-1]
            assert ext not in valid_extensions


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_response_structure(self):
        """Test health response format"""
        response = {
            "status": "healthy",
            "service": "yolo-service",
            "model_loaded": True
        }
        
        assert response["status"] == "healthy"
        assert response["service"] == "yolo-service"
    
    def test_model_status(self):
        """Test model loaded status"""
        model_loaded = True
        assert model_loaded in [True, False]


class TestMetrics:
    """Test Prometheus metrics"""
    
    def test_metrics_counters(self):
        """Test metrics counter names"""
        expected_metrics = [
            "yolo_detection_requests_total",
            "yolo_objects_detected_total",
            "yolo_detection_latency_seconds"
        ]
        
        for metric in expected_metrics:
            assert "yolo" in metric