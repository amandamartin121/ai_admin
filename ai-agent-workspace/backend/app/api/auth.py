"""
Authentication API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Annotated

from app.database.session import get_db
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    Token,
    ChangePasswordRequest,
    UserResponse,
    SessionList,
)
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.security.dependencies import get_current_user
from app.models.user import User
from app.models.audit import AuditAction

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Register a new user account."""
    auth_service = AuthService(db)
    audit_service = AuditService(db)
    
    # Check if registration is allowed (could be disabled by admin)
    user = await auth_service.register_user(
        email=request.email,
        username=request.username,
        password=request.password,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Log registration
    await audit_service.log_action(
        action=AuditAction.USER_CREATED,
        actor_user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    
    return user


@router.post("/login", response_model=Token)
async def login(
    request: LoginRequest,
    req: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Login and receive access/refresh tokens."""
    auth_service = AuthService(db)
    audit_service = AuditService(db)
    
    result = await auth_service.authenticate_user(
        email=request.email,
        password=request.password,
    )
    
    if not result:
        # Log failed login attempt
        await audit_service.log_action(
            action=AuditAction.LOGIN_FAILED,
            resource_type="auth",
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent"),
            status="failure",
            metadata={"email": request.email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    user, access_token, refresh_token = result
    
    # Create session
    await auth_service.create_session(
        user_id=user.id,
        refresh_token=refresh_token,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent"),
    )
    
    # Log successful login
    await audit_service.log_action(
        action=AuditAction.LOGIN_SUCCESS,
        actor_user_id=user.id,
        resource_type="auth",
        ip_address=req.client.host if req.client else None,
    )
    
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: dict,
    req: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Refresh access token using refresh token."""
    auth_service = AuthService(db)
    
    refresh_token = request.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required",
        )
    
    result = await auth_service.refresh_tokens(
        refresh_token=refresh_token,
        ip_address=req.client.host if req.client else None,
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    new_access_token, new_refresh_token, _ = result
    
    return Token(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post("/logout")
async def logout(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
):
    """Logout and revoke current session."""
    auth_service = AuthService(db)
    audit_service = AuditService(db)
    
    # Revoke all sessions (or just current one based on requirements)
    await auth_service.revoke_all_sessions(current_user.id)
    
    # Log logout
    await audit_service.log_action(
        action=AuditAction.LOGOUT,
        actor_user_id=current_user.id,
        resource_type="auth",
        ip_address=request.client.host if request.client else None,
    )
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current authenticated user information."""
    return current_user


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Change current user's password."""
    auth_service = AuthService(db)
    audit_service = AuditService(db)
    
    success = await auth_service.change_password(
        user_id=current_user.id,
        current_password=request.current_password,
        new_password=request.new_password,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    # Log password change
    await audit_service.log_action(
        action=AuditAction.PASSWORD_CHANGED,
        actor_user_id=current_user.id,
        resource_type="user",
        resource_id=current_user.id,
    )
    
    return {"message": "Password changed successfully"}


@router.get("/sessions", response_model=SessionList)
async def get_user_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get all active sessions for current user."""
    auth_service = AuthService(db)
    sessions = await auth_service.get_user_sessions(current_user.id)
    
    return SessionList(sessions=sessions, total=len(sessions))


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Revoke a specific session."""
    auth_service = AuthService(db)
    
    success = await auth_service.revoke_session(
        session_id=session_id,
        user_id=current_user.id,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    return {"message": "Session revoked successfully"}
