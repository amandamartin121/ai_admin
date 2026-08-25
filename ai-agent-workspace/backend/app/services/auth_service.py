"""
Authentication service for user authentication and session management.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from typing import Optional, Tuple
import hashlib

from app.models.user import User
from app.models.session import Session as SessionModel
from app.security.password import verify_password, get_password_hash, needs_rehash
from app.security.jwt import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    hash_refresh_token,
)


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, db: Session):
        self.db = db

    async def authenticate_user(
        self, email: str, password: str
    ) -> Optional[Tuple[User, dict, dict]]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: User's plain text password
            
        Returns:
            Tuple of (user, access_token, refresh_token) if successful, None otherwise
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user or not user.is_active:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # Check if password needs rehashing (for upgrading hash parameters)
        if needs_rehash(user.hashed_password):
            user.hashed_password = get_password_hash(password)
            self.db.commit()
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        self.db.commit()
        
        # Generate tokens
        access_token = create_access_token(data={"sub": user.id})
        refresh_token = create_refresh_token(data={"sub": user.id})
        
        return (user, access_token, refresh_token)

    async def register_user(
        self, email: str, username: str, password: str
    ) -> Optional[User]:
        """
        Register a new user.
        
        Args:
            email: User's email address
            username: User's display name
            password: User's plain text password
            
        Returns:
            The created user if successful, None if email already exists
        """
        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            return None
        
        # Create user
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_superuser=False,
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user

    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> bool:
        """
        Change a user's password.
        
        Args:
            user_id: User's ID
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if successful, False otherwise
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            return False
        
        if not verify_password(current_password, user.hashed_password):
            return False
        
        # Set new password
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        
        return True

    async def create_session(
        self,
        user_id: str,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> SessionModel:
        """
        Create a new session for a user.
        
        Args:
            user_id: User's ID
            refresh_token: The refresh token string
            ip_address: Client IP address
            user_agent: Client user agent string
            
        Returns:
            The created session
        """
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=7  # Should match JWT_REFRESH_EXPIRE_DAYS
        )
        
        session = SessionModel(
            user_id=user_id,
            refresh_token_hash=hash_refresh_token(refresh_token),
            is_active=True,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session

    async def revoke_session(self, session_id: str, user_id: str) -> bool:
        """
        Revoke a session.
        
        Args:
            session_id: Session ID to revoke
            user_id: User ID for ownership check
            
        Returns:
            True if successful, False otherwise
        """
        session = (
            self.db.query(SessionModel)
            .filter(SessionModel.id == session_id, SessionModel.user_id == user_id)
            .first()
        )
        
        if not session:
            return False
        
        session.is_active = False
        self.db.commit()
        
        return True

    async def revoke_all_sessions(self, user_id: str) -> int:
        """
        Revoke all sessions for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            Number of sessions revoked
        """
        result = (
            self.db.query(SessionModel)
            .filter(SessionModel.user_id == user_id, SessionModel.is_active == True)
            .update({"is_active": False})
        )
        self.db.commit()
        
        return result

    async def get_user_sessions(self, user_id: str) -> list:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            List of session information
        """
        sessions = (
            self.db.query(SessionModel)
            .filter(SessionModel.user_id == user_id, SessionModel.is_active == True)
            .order_by(SessionModel.created_at.desc())
            .all()
        )
        
        return [
            {
                "id": s.id,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent[:100] if s.user_agent else None,
                "expires_at": s.expires_at,
                "last_used_at": s.last_used_at,
                "created_at": s.created_at,
            }
            for s in sessions
        ]

    async def refresh_tokens(
        self, refresh_token: str, ip_address: Optional[str] = None
    ) -> Optional[Tuple[str, str, User]]:
        """
        Refresh access and refresh tokens using a valid refresh token.
        
        Args:
            refresh_token: The current refresh token
            ip_address: Client IP address
            
        Returns:
            Tuple of (new_access_token, new_refresh_token, user) if successful
        """
        # Verify refresh token
        payload = verify_refresh_token(refresh_token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Get user
        user = self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            return None
        
        # Verify session exists and is active
        session = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.user_id == user_id,
                SessionModel.refresh_token_hash == hash_refresh_token(refresh_token),
                SessionModel.is_active == True,
            )
            .first()
        )
        
        if not session:
            return None
        
        # Update session last used
        session.last_used_at = datetime.now(timezone.utc)
        
        # Generate new tokens
        new_access_token = create_access_token(data={"sub": user.id})
        new_refresh_token = create_refresh_token(data={"sub": user.id})
        
        # Update session with new refresh token hash
        session.refresh_token_hash = hash_refresh_token(new_refresh_token)
        self.db.commit()
        
        return (new_access_token, new_refresh_token, user)
