"""
Unit tests for Postprocessor Service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestPostprocessorService:
    """Test suite for Postprocessor service"""
    
    @pytest.fixture
    def service(self):
        """Create service instance with mocked dependencies"""
        with patch('app.main.MongoClient'):
            from app.main import PostprocessorService
            service = PostprocessorService()
            service.collection = MagicMock()
            yield service
    
    def test_postprocess_data_adds_fields(self, service):
        """Test that postprocessing adds required fields"""
        data = {
            "objects": {"person": 2, "dog": 1},
            "description": "Test description"
        }
        
        result = service.postprocess_data(data)
        
        assert result["postprocessed"] is True
        assert "postprocessed_at" in result
        assert "statistics" in result
        assert result["statistics"]["total_objects"] == 3
    
    def test_postprocess_data_counts_unique_classes(self, service):
        """Test unique class counting"""
        data = {
            "objects": {"person": 5, "car": 2, "dog": 3}
        }
        
        result = service.postprocess_data(data)
        
        assert result["statistics"]["unique_classes"] == 3
    
    def test_postprocess_empty_objects(self, service):
        """Test postprocessing with no objects"""
        data = {"objects": {}}
        
        result = service.postprocess_data(data)
        
        assert result["statistics"]["total_objects"] == 0
        assert result["statistics"]["unique_classes"] == 0
    
    def test_categorize_people(self, service):
        """Test categorization of people"""
        objects = {"person": 3}
        
        categories = service._categorize_objects(objects)
        
        assert "people" in categories
        assert categories["people"][0]["count"] == 3
    
    def test_categorize_vehicles(self, service):
        """Test categorization of vehicles"""
        objects = {"car": 2, "truck": 1, "bicycle": 1}
        
        categories = service._categorize_objects(objects)
        
        assert "vehicles" in categories
        assert len(categories["vehicles"]) == 3
    
    def test_categorize_animals(self, service):
        """Test categorization of animals"""
        objects = {"dog": 1, "cat": 2}
        
        categories = service._categorize_objects(objects)
        
        assert "animals" in categories
        assert len(categories["animals"]) == 2
    
    def test_categorize_unknown_objects(self, service):
        """Test categorization of unknown objects"""
        objects = {"unknown_thing": 1}
        
        categories = service._categorize_objects(objects)
        
        assert "other" in categories
        assert categories["other"][0]["name"] == "unknown_thing"
    
    def test_calculate_avg_confidence(self, service):
        """Test average confidence calculation"""
        confidence_scores = {
            "person": [0.9, 0.8],
            "dog": [0.85]
        }
        
        avg = service._calculate_avg_confidence(confidence_scores)
        
        expected = (0.9 + 0.8 + 0.85) / 3
        assert abs(avg - expected) < 0.0001
    
    def test_calculate_avg_confidence_empty(self, service):
        """Test average confidence with empty data"""
        avg = service._calculate_avg_confidence({})
        assert avg == 0.0
    
    def test_save_postprocessed(self, service):
        """Test saving postprocessed data"""
        service.collection.insert_one.return_value.inserted_id = "test-id"
        
        data = {"test": "data"}
        result = service.save_postprocessed(data)
        
        assert result == "test-id"
        service.collection.insert_one.assert_called_once()
    
    def test_process_message_valid(self, service):
        """Test processing a valid message"""
        service.collection.insert_one.return_value.inserted_id = "test-id"
        
        message = json.dumps({
            "objects": {"person": 1},
            "description": "test"
        }).encode()
        
        # Should not raise
        service.process_message(message)
        
        service.collection.insert_one.assert_called_once()
    
    def test_process_message_invalid_json(self, service):
        """Test processing invalid JSON"""
        message = b"not valid json"
        
        # Should not raise, just log error
        service.process_message(message)
        
        # Should not have saved anything
        service.collection.insert_one.assert_not_called()


class TestCategorization:
    """Test object categorization logic"""
    
    @pytest.fixture
    def service(self):
        """Create service for categorization tests"""
        with patch('app.main.MongoClient'):
            from app.main import PostprocessorService
            yield PostprocessorService()
    
    def test_mixed_categories(self, service):
        """Test objects from multiple categories"""
        objects = {
            "person": 2,
            "car": 1,
            "dog": 1,
            "laptop": 1
        }
        
        categories = service._categorize_objects(objects)
        
        assert "people" in categories
        assert "vehicles" in categories
        assert "animals" in categories
        assert "electronics" in categories
    
    def test_empty_categories_removed(self, service):
        """Test that empty categories are not included"""
        objects = {"person": 1}
        
        categories = service._categorize_objects(objects)
        
        # Should only have 'people', not empty categories
        assert list(categories.keys()) == ["people"]


class TestStatistics:
    """Test statistics calculation"""
    
    @pytest.fixture
    def service(self):
        """Create service for statistics tests"""
        with patch('app.main.MongoClient'):
            from app.main import PostprocessorService
            yield PostprocessorService()
    
    def test_statistics_structure(self, service):
        """Test statistics dictionary structure"""
        data = {
            "objects": {"person": 2, "car": 1},
            "confidence_scores": {"person": [0.9, 0.8], "car": [0.7]}
        }
        
        result = service.postprocess_data(data)
        stats = result["statistics"]
        
        assert "total_objects" in stats
        assert "unique_classes" in stats
        assert "categories" in stats
        assert "average_confidence" in stats
    
    def test_preserves_original_data(self, service):
        """Test that original data is preserved"""
        data = {
            "objects": {"person": 1},
            "description": "original description",
            "custom_field": "should be preserved"
        }
        
        result = service.postprocess_data(data)
        
        assert result["description"] == "original description"
        assert result["custom_field"] == "should be preserved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
