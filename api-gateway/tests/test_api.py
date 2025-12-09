"""
Unit tests for API Gateway
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import io


class TestAPIGateway:
    """Test suite for API Gateway"""
    
    @pytest.fixture
    def mock_services(self):
        """Mock all external services"""
        with patch('app.main.http_client') as mock_http, \
             patch('app.db_service.MongoClient') as mock_mongo, \
             patch('app.firebase_service.firebase_admin') as mock_firebase, \
             patch('app.rabbitmq_service.pika') as mock_pika, \
             patch('app.auth.firebase_admin') as mock_auth:
            
            # Setup mock responses
            mock_http.post = AsyncMock()
            mock_http.get = AsyncMock()
            
            yield {
                'http': mock_http,
                'mongo': mock_mongo,
                'firebase': mock_firebase,
                'pika': mock_pika,
                'auth': mock_auth
            }
    
    @pytest.fixture
    def client(self, mock_services):
        """Create test client"""
        from app.main import app
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "running" in data["message"].lower()
    
    def test_health_endpoint(self, client, mock_services):
        """Test health check endpoint"""
        # Mock service health checks
        mock_services['http'].get.return_value = Mock(status_code=200)
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "api_requests_total" in response.text
    
    def test_detect_requires_auth(self, client):
        """Test that /detect requires authentication"""
        response = client.post("/detect")
        assert response.status_code in [401, 403, 422]
    
    def test_generate_requires_auth(self, client):
        """Test that /generate requires authentication"""
        response = client.post(
            "/generate",
            json={"prompt": "test"}
        )
        assert response.status_code in [401, 403]
    
    def test_history_requires_auth(self, client):
        """Test that /history requires authentication"""
        response = client.get("/history")
        assert response.status_code in [401, 403]


class TestAuthMiddleware:
    """Test authentication middleware"""
    
    def test_missing_auth_header(self):
        """Test request without auth header"""
        from app.auth import verify_firebase_token
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            verify_firebase_token("")
        
        assert exc.value.status_code == 401
    
    def test_invalid_token_format(self):
        """Test invalid token format"""
        from app.auth import verify_firebase_token
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException):
            verify_firebase_token("invalid-token")


class TestDatabaseService:
    """Test database service"""
    
    @pytest.fixture
    def db_service(self):
        """Create database service with mocked client"""
        with patch('app.db_service.MongoClient') as mock_client:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_client.return_value.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            
            from app.db_service import DatabaseService
            service = DatabaseService()
            service._client = mock_client.return_value
            service._db = mock_db
            service._history_collection = mock_collection
            
            yield service, mock_collection
    
    def test_save_record(self, db_service):
        """Test saving a record"""
        service, mock_collection = db_service
        mock_collection.insert_one.return_value.inserted_id = "test-id"
        
        result = service.save_record(
            {"person": 1},
            "A person in the image",
            user_id="user123"
        )
        
        assert result == "test-id"
        mock_collection.insert_one.assert_called_once()
    
    def test_get_all_records(self, db_service):
        """Test retrieving all records"""
        service, mock_collection = db_service
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value = [
            {"objects": {"dog": 1}, "description": "test"}
        ]
        mock_collection.find.return_value = mock_cursor
        
        records = service.get_all_records()
        
        assert len(records) == 1


class TestFirebaseService:
    """Test Firebase service"""
    
    def test_save_record_when_unavailable(self):
        """Test saving when Firebase is not available"""
        with patch('app.firebase_service.firebase_admin'):
            from app.firebase_service import FirebaseService
            service = FirebaseService()
            service._initialized = True
            service._collection = None
            
            result = service.save_record({}, "test")
            assert result is None
    
    def test_get_all_when_unavailable(self):
        """Test get_all when Firebase is not available"""
        with patch('app.firebase_service.firebase_admin'):
            from app.firebase_service import FirebaseService
            service = FirebaseService()
            service._initialized = True
            service._collection = None
            
            result = service.get_all()
            assert result == []


class TestRabbitMQService:
    """Test RabbitMQ service"""
    
    def test_publish_message_structure(self):
        """Test that publish creates correct message structure"""
        with patch('app.rabbitmq_service.pika') as mock_pika:
            mock_connection = MagicMock()
            mock_channel = MagicMock()
            mock_pika.BlockingConnection.return_value = mock_connection
            mock_connection.channel.return_value = mock_channel
            mock_channel.is_open = True
            
            from app.rabbitmq_service import RabbitMQService
            service = RabbitMQService()
            
            result = service.publish_message({"test": "data"})
            
            assert mock_channel.basic_publish.called


class TestInputValidation:
    """Test input validation"""
    
    @pytest.fixture
    def client(self):
        """Create test client with mocked auth"""
        with patch('app.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = {"uid": "test-user"}
            
            from app.main import app
            yield TestClient(app)
    
    def test_generate_empty_prompt_fails(self, client):
        """Test that empty prompt fails validation"""
        response = client.post(
            "/generate",
            json={"prompt": ""},
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 422
    
    def test_generate_max_tokens_bounds(self, client):
        """Test max_tokens validation"""
        response = client.post(
            "/generate",
            json={"prompt": "test", "max_tokens": 1000},
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
