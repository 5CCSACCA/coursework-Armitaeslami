"""Unit tests for LLM Service (BitNet)"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient


class TestLLMService:
    
    @pytest.fixture
    def client(self):
        from app.main import app, llm_model
        llm_model.is_loaded = True
        llm_model.use_fallback = True
        llm_model.model_name = "bitnet-fallback (test)"
        yield TestClient(app)
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "LLM" in response.json()["message"]
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "llm-service"
        assert "model_name" in data
    
    def test_generate_valid_request(self, client):
        """Test text generation with valid request"""
        response = client.post(
            "/generate",
            json={
                "prompt": "Describe a sunny day",
                "max_tokens": 50,
                "temperature": 0.7
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "prompt" in data
        assert "response" in data
        assert "tokens_generated" in data
        assert "model" in data
    
    def test_generate_empty_prompt(self, client):
        response = client.post(
            "/generate",
            json={
                "prompt": "",
                "max_tokens": 50
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_generate_max_tokens_limit(self, client):
        response = client.post(
            "/generate",
            json={
                "prompt": "Test prompt",
                "max_tokens": 1000  # Above limit
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_describe_objects_valid(self, client):
        response = client.post(
            "/describe",
            json={
                "objects": {"person": 2, "dog": 1},
                "style": "descriptive"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "description" in data
        assert "objects" in data
        assert data["objects"]["person"] == 2
    
    def test_describe_objects_empty(self, client):
        response = client.post(
            "/describe",
            json={
                "objects": {},
                "style": "descriptive"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "No objects" in data["description"]
    
    def test_describe_objects_brief_style(self, client):
        response = client.post(
            "/describe",
            json={
                "objects": {"car": 3},
                "style": "brief"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "Detected:" in data["description"]
    
    def test_describe_objects_detailed_style(self, client):
        response = client.post(
            "/describe",
            json={
                "objects": {"person": 1, "dog": 2},
                "style": "detailed"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data["description"].lower()
    
    def test_metrics_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "llm_generation_requests_total" in response.text
    
    def test_models_endpoint(self, client):
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert "current_model" in data
        assert "supported_models" in data


class TestBitNetModel:
    
    def test_describe_single_object(self):
        from app.main import BitNetModel
        model = BitNetModel()
        model.is_loaded = True
        
        result = model.describe_objects({"dog": 1})
        assert "1 dog" in result
    
    def test_describe_multiple_objects(self):
        from app.main import BitNetModel
        model = BitNetModel()
        model.is_loaded = True
        
        result = model.describe_objects({"person": 2, "car": 1})
        assert "2 persons" in result or "2 people" in result.lower()
        assert "1 car" in result
    
    def test_describe_empty_objects(self):
        from app.main import BitNetModel
        model = BitNetModel()
        model.is_loaded = True
        
        result = model.describe_objects({})
        assert "No objects" in result
    
    def test_rule_based_fallback(self):
        from app.main import BitNetModel
        model = BitNetModel()
        model.is_loaded = True
        model.model = None
        model.tokenizer = None
        
        response, tokens = model.generate("Test prompt")
        assert isinstance(response, str)
        assert isinstance(tokens, int)
        assert tokens > 0


class TestInputValidation:
    
    @pytest.fixture
    def client(self):
        from app.main import app, llm_model
        llm_model.is_loaded = True
        yield TestClient(app)
    
    def test_temperature_bounds(self, client):
        # Too high
        response = client.post(
            "/generate",
            json={"prompt": "test", "temperature": 3.0}
        )
        assert response.status_code == 422
        
        # Too low
        response = client.post(
            "/generate",
            json={"prompt": "test", "temperature": -1.0}
        )
        assert response.status_code == 422
    
    def test_max_tokens_bounds(self, client):
        # Too high
        response = client.post(
            "/generate",
            json={"prompt": "test", "max_tokens": 1000}
        )
        assert response.status_code == 422
        
        # Zero
        response = client.post(
            "/generate",
            json={"prompt": "test", "max_tokens": 0}
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
