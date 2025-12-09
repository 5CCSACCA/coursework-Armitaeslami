"""
Firebase Service for Cloud Storage

Handles storage of detection records in Firebase Firestore.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import firebase_admin
from firebase_admin import credentials, firestore

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FirebaseService:
    """Firebase Firestore service for storing detection records"""
    
    def __init__(self):
        self._db = None
        self._collection = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize Firebase connection"""
        if self._initialized:
            return
        
        try:
            key_path = settings.firebase_key_path
            
            if not os.path.exists(key_path):
                logger.warning(f"Firebase key not found at {key_path}")
                self._initialized = True
                return
            
            if not firebase_admin._apps:
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred)
            
            self._db = firestore.client()
            self._collection = self._db.collection("detections")
            self._initialized = True
            logger.info("Firebase Firestore initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Firebase: {e}")
            self._initialized = True
    
    @property
    def collection(self):
        """Get Firestore collection"""
        if not self._initialized:
            self._initialize()
        return self._collection
    
    @property
    def is_available(self) -> bool:
        """Check if Firebase is available"""
        self._initialize()
        return self._collection is not None
    
    def save_record(
        self,
        objects: Dict[str, int],
        description: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Save a detection record to Firestore.
        
        Args:
            objects: Dictionary of detected objects and counts
            description: Generated description
            user_id: Optional user ID
            metadata: Optional additional metadata
        
        Returns:
            Document ID or None if failed
        """
        if not self.is_available:
            logger.warning("Firebase not available - skipping save")
            return None
        
        try:
            entry = {
                "objects": objects,
                "description": description,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "time": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "metadata": metadata or {}
            }
            
            doc_ref = self.collection.add(entry)
            doc_id = doc_ref[1].id
            logger.info(f"Saved to Firebase with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error saving to Firebase: {e}")
            return None
    
    def get_all(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all detection records from Firestore.
        
        Args:
            user_id: Optional filter by user ID
            limit: Maximum number of records
        
        Returns:
            List of records with their document IDs
        """
        if not self.is_available:
            logger.warning("Firebase not available")
            return []
        
        try:
            query = self.collection
            
            if user_id:
                query = query.where("user_id", "==", user_id)
            
            query = query.order_by(
                "timestamp",
                direction=firestore.Query.DESCENDING
            ).limit(limit)
            
            docs = query.stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                # Convert timestamp to string if present
                if "timestamp" in data and data["timestamp"]:
                    data["timestamp"] = data["timestamp"].isoformat()
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving from Firebase: {e}")
            return []
    
    def get_record(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific record by document ID.
        
        Args:
            doc_id: Firestore document ID
        
        Returns:
            Record data or None if not found
        """
        if not self.is_available:
            return None
        
        try:
            doc = self.collection.document(doc_id).get()
            
            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {e}")
            return None
    
    def update_record(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """
        Update a record in Firestore.
        
        Args:
            doc_id: Document ID to update
            data: Data to update
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            # Don't allow updating system fields
            safe_data = {
                k: v for k, v in data.items()
                if k not in ["id", "timestamp", "time"]
            }
            safe_data["updated_at"] = firestore.SERVER_TIMESTAMP
            
            self.collection.document(doc_id).update(safe_data)
            logger.info(f"Updated Firebase document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            return False
    
    def delete_record(self, doc_id: str) -> bool:
        """
        Delete a record from Firestore.
        
        Args:
            doc_id: Document ID to delete
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            self.collection.document(doc_id).delete()
            logger.info(f"Deleted Firebase document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def health_check(self) -> bool:
        """
        Check if Firebase connection is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            # Try to access the collection
            self.collection.limit(1).get()
            return True
        except Exception:
            return False


# Global instance
firebase_service = FirebaseService()


def get_firebase_service() -> FirebaseService:
    """Dependency for getting Firebase service"""
    return firebase_service
