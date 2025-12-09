"""
Unit tests for YOLO Object Detection Service
"""

import pytest
import io
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from fastapi.testclient import TestClient


class TestYoloService:
    
    @pytest.fixture
    def client(self):
        with patch('app.main.YOLO') as mock_yolo:
            # Setup mock model
            mock_model = MagicMock()
            mock_yolo.return_value = mock_model
            
            # Setup mock results
            mock_result = MagicMock()
            mock_result.boxes.cls.tolist.return_value = [0, 0, 16]  # 2 persons, 1 dog
            mock_result.boxes.conf.tolist.return_value = [0.95, 0.87, 0.92]
            mock_result.names = {0: 'person', 16: 'dog'}
            mock_model.return_value = [mock_result]
            
            from app.main import app
            yield TestClient(app)
    
    @pytest.fixture
    def sample_image(self):
        img = Image.new('RGB', (640, 480), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "YOLO" in response.json()["message"]
    
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "yolo-service"
    
    def test_detect_valid_image(self, client, sample_image):
        response = client.post(
            "/detect",
            files={"file": ("test.jpg", sample_image, "image/jpeg")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "objects" in data
        assert "confidence_scores" in data
        assert "total_objects" in data
    
    def test_detect_invalid_file_type(self, client):
        response = client.post(
            "/detect",
            files={"file": ("test.txt", b"not an image", "text/plain")}
        )
        assert response.status_code == 400
        assert "image" in response.json()["detail"].lower()
    
    def test_detect_returns_correct_structure(self, client, sample_image):
        response = client.post(
            "/detect",
            files={"file": ("test.jpg", sample_image, "image/jpeg")}
        )
        data = response.json()
        
        assert isinstance(data["objects"], dict)
        for key, value in data["objects"].items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        
        assert isinstance(data["confidence_scores"], dict)
        for key, values in data["confidence_scores"].items():
            assert isinstance(key, str)
            assert isinstance(values, list)
            for v in values:
                assert isinstance(v, float)
                assert 0 <= v <= 1
    
    def test_metrics_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "yolo_detection_requests_total" in response.text


class TestImageProcessing:
    
    def test_rgb_conversion(self):
        rgba_img = Image.new('RGBA', (100, 100), color='red')
        rgb_img = rgba_img.convert('RGB')
        assert rgb_img.mode == 'RGB'
    
    def test_grayscale_conversion(self):
        gray_img = Image.new('L', (100, 100), color=128)
        rgb_img = gray_img.convert('RGB')
        assert rgb_img.mode == 'RGB'


class TestDetectionResult:
    
    def test_valid_result(self):
        from app.main import DetectionResult
        
        result = DetectionResult(
            objects={"person": 2, "dog": 1},
            confidence_scores={"person": [0.95, 0.87], "dog": [0.92]},
            total_objects=3
        )
        
        assert result.objects["person"] == 2
        assert result.total_objects == 3
    
    def test_empty_result(self):
        from app.main import DetectionResult
        
        result = DetectionResult(
            objects={},
            confidence_scores={},
            total_objects=0
        )
        
        assert len(result.objects) == 0
        assert result.total_objects == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
