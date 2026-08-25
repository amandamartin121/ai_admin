"""
Security dependencies for FastAPI routes.
Provides authentication and authorization utilities.
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.security.jwt import verify_access_token
from app.models.user import User
from app.models.session import Session as SessionModel


# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        The authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify access token
    payload = verify_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_permission(permission_name: str):
    """
    Create a dependency that requires a specific permission.
    
    Args:
        permission_name: The permission name required (e.g., 'users.view')
        
    Returns:
        A dependency function that checks for the permission
    """
    
    async def check_permission(
        current_user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> User:
        from app.services.permission_service import PermissionService
        
        permission_service = PermissionService(db)
        has_permission = await permission_service.user_has_permission(
            current_user.id, permission_name
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission_name}",
            )
        
        return current_user
    
    return check_permission


def require_admin():
    """
    Create a dependency that requires admin privileges.
    
    Returns:
        A dependency function that checks for admin role
    """
    
    async def check_admin(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if not current_user.is_superuser:
            # Check if user has ADMIN role
            from app.services.role_service import RoleService
            
            # For now, just check is_superuser flag
            # This will be enhanced with proper role checking
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required",
            )
        
        return current_user
    
    return check_admin


def get_optional_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> Optional[User]:
    """
    Dependency to optionally get the current user if authenticated.
    
    Returns None if not authenticated instead of raising an exception.
    Useful for endpoints that work differently for authenticated users.
    """
    try:
        return get_current_user.__wrapped__(credentials, db)
    except HTTPException:
        return None
