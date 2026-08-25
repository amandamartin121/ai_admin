"""
JWT token management for authentication.
Handles creation, verification, and refresh of access and refresh tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError, ExpiredSignatureError
import hashlib
import secrets

from app.core.config import settings


# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

# Algorithm for JWT
ALGORITHM = "HS256"


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to include in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_expire_minutes
        )
    
    to_encode.update({"exp": expire, "type": TOKEN_TYPE_ACCESS})
    
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: Payload data to include in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_expire_days
        )
    
    to_encode.update({"exp": expire, "type": TOKEN_TYPE_REFRESH})
    
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, expected_type: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token and return its payload.
    
    Args:
        token: The JWT token to verify
        expected_type: Expected token type ('access' or 'refresh')
        
    Returns:
        Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        
        # Verify token type
        token_type = payload.get("type")
        if token_type != expected_type:
            return None
            
        return payload
    except (ExpiredSignatureError, JWTError):
        return None


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify an access token."""
    return verify_token(token, TOKEN_TYPE_ACCESS)


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a refresh token."""
    return verify_token(token, TOKEN_TYPE_REFRESH)


def hash_refresh_token(refresh_token: str) -> str:
    """
    Create a hash of a refresh token for secure storage.
    
    We store hashes instead of raw tokens in the database.
    """
    return hashlib.sha256(refresh_token.encode()).hexdigest()


def generate_token_jti() -> str:
    """Generate a unique token ID for tracking/revocation."""
    return secrets.token_urlsafe(16)
