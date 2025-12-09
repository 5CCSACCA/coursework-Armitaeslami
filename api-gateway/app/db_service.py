"""
Database Service using MongoDB

Handles persistence of detection records and history.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseService:
    """MongoDB database service for storing detection records"""
    
    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None
        self._history_collection: Optional[Collection] = None
        self._postprocessed_collection: Optional[Collection] = None
    
    def _get_client(self) -> MongoClient:
        """Get or create MongoDB client"""
        if self._client is None:
            try:
                self._client = MongoClient(
                    settings.mongodb_uri,
                    serverSelectionTimeoutMS=5000
                )
                # Test connection
                self._client.admin.command('ping')
                logger.info("Connected to MongoDB successfully")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
        return self._client
    
    def _get_db(self) -> Database:
        """Get or create database reference"""
        if self._db is None:
            client = self._get_client()
            self._db = client[settings.mongodb_database]
        return self._db
    
    @property
    def history_collection(self) -> Collection:
        """Get history collection"""
        if self._history_collection is None:
            self._history_collection = self._get_db()["history"]
        return self._history_collection
    
    @property
    def postprocessed_collection(self) -> Collection:
        """Get postprocessed collection"""
        if self._postprocessed_collection is None:
            self._postprocessed_collection = self._get_db()["postprocessed"]
        return self._postprocessed_collection
    
    def save_record(
        self,
        objects_found: Dict[str, int],
        description_text: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save a detection record to the database.
        
        Args:
            objects_found: Dictionary of detected objects and counts
            description_text: Generated description of the image
            user_id: Optional user ID who made the request
            metadata: Optional additional metadata
        
        Returns:
            String ID of the inserted document
        """
        record = {
            "objects": objects_found,
            "description": description_text,
            "timestamp": datetime.utcnow(),
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id,
            "metadata": metadata or {}
        }
        
        result = self.history_collection.insert_one(record)
        logger.info(f"Saved record with ID: {result.inserted_id}")
        return str(result.inserted_id)
    
    def get_all_records(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all detection records.
        
        Args:
            user_id: Optional filter by user ID
            limit: Maximum number of records to return
            skip: Number of records to skip (pagination)
        
        Returns:
            List of detection records
        """
        query = {}
        if user_id:
            query["user_id"] = user_id
        
        cursor = self.history_collection.find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(limit)
        
        return list(cursor)
    
    def get_record_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific record by ID.
        
        Args:
            record_id: MongoDB document ID
        
        Returns:
            Record document or None if not found
        """
        from bson import ObjectId
        
        try:
            record = self.history_collection.find_one(
                {"_id": ObjectId(record_id)},
                {"_id": 0}
            )
            return record
        except Exception as e:
            logger.error(f"Error retrieving record {record_id}: {e}")
            return None
    
    def delete_record(self, record_id: str) -> bool:
        """
        Delete a record by ID.
        
        Args:
            record_id: MongoDB document ID
        
        Returns:
            True if deleted, False otherwise
        """
        from bson import ObjectId
        
        try:
            result = self.history_collection.delete_one(
                {"_id": ObjectId(record_id)}
            )
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting record {record_id}: {e}")
            return False
    
    def get_postprocessed_records(
        self,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve postprocessed records.
        
        Args:
            limit: Maximum number of records
            skip: Number to skip
        
        Returns:
            List of postprocessed records
        """
        cursor = self.postprocessed_collection.find(
            {},
            {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(limit)
        
        return list(cursor)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with collection statistics
        """
        return {
            "history_count": self.history_collection.count_documents({}),
            "postprocessed_count": self.postprocessed_collection.count_documents({}),
            "database": settings.mongodb_database
        }
    
    def health_check(self) -> bool:
        """
        Check if database connection is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            self._get_client().admin.command('ping')
            return True
        except Exception:
            return False
    
    def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")


# Global instance
db_service = DatabaseService()


def get_db_service() -> DatabaseService:
    """Dependency for getting database service"""
    return db_service
