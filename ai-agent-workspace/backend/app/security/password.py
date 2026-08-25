"""
Security utilities for password hashing and verification.
Uses Argon2 for secure password storage.
"""

from passlib.context import CryptContext
from typing import Optional

# Configure Argon2 context with recommended settings
pwd_context = CryptContext(
    schemes=["argon2"],
    argon2__time_cost=3,
    argon2__memory_cost=65536,
    argon2__parallelism=4,
    deprecated="auto",
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The Argon2-hashed password
        
    Returns:
        True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The Argon2-hashed password
    """
    return pwd_context.hash(password)


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be rehashed.
    
    This is useful for upgrading hash parameters over time.
    
    Args:
        hashed_password: The existing hash to check
        
    Returns:
        True if the hash should be regenerated with current parameters
    """
    return pwd_context.needs_update(hashed_password)
