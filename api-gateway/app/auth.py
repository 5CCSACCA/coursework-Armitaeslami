"""
Authentication Service using Firebase

Handles user authentication and token verification using Firebase Auth.
"""

import os
import logging
from typing import Optional

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Security scheme for Swagger UI
security = HTTPBearer()

# Initialize Firebase Admin SDK
_firebase_initialized = False


def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized"""
    global _firebase_initialized
    
    if _firebase_initialized:
        return
    
    try:
        if not firebase_admin._apps:
            key_path = settings.firebase_key_path
            
            if os.path.exists(key_path):
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                logger.warning(f"Firebase key not found at {key_path}. Authentication will use mock mode.")
        
        _firebase_initialized = True
        
    except Exception as e:
        logger.error(f"Error initializing Firebase: {e}")
        _firebase_initialized = True  # Mark as initialized to avoid retry loops


def verify_firebase_token(token: str) -> dict:
    """
    Verify a Firebase ID token.
    
    Args:
        token: Firebase ID token string
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    initialize_firebase()
    
    try:
        # For testing/development when Firebase is not configured
        if not firebase_admin._apps:
            logger.warning("Firebase not configured - using mock authentication")
            if token == "test-token" or token.startswith("mock-"):
                return {"uid": "test-user", "email": "test@example.com"}
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token (mock mode)"
            )
        
        # Verify the token with Firebase
        decoded_token = auth.verify_id_token(token)
        return decoded_token
        
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired"
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has been revoked"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency for getting the current authenticated user.
    
    Args:
        credentials: HTTP Bearer credentials from request header
    
    Returns:
        Decoded user information from token
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    token = credentials.credentials
    return verify_firebase_token(token)


class AuthenticatedUser:
    """Represents an authenticated user"""
    
    def __init__(self, token_data: dict):
        self.uid = token_data.get("uid")
        self.email = token_data.get("email")
        self.email_verified = token_data.get("email_verified", False)
        self.name = token_data.get("name")
        self.picture = token_data.get("picture")
        self._raw = token_data
    
    @property
    def is_authenticated(self) -> bool:
        return self.uid is not None
    
    def __repr__(self):
        return f"AuthenticatedUser(uid={self.uid}, email={self.email})"


async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AuthenticatedUser:
    """
    Dependency for getting an AuthenticatedUser instance.
    
    Returns:
        AuthenticatedUser instance with user information
    """
    token_data = await get_current_user(credentials)
    return AuthenticatedUser(token_data)


# Optional authentication (for endpoints that work with or without auth)
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[AuthenticatedUser]:
    """
    Dependency for optional authentication.
    
    Returns:
        AuthenticatedUser if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token_data = verify_firebase_token(credentials.credentials)
        return AuthenticatedUser(token_data)
    except HTTPException:
        return None
