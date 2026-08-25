"""
Admin API routes for user and system management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from datetime import datetime, timezone

from app.database.session import get_db
from app.schemas.auth import (
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserResponse,
    RoleResponse,
    PermissionResponse,
)
from app.security.dependencies import get_current_user
from app.models.user import User
from app.services.role_service import RoleService
from app.services.permission_service import PermissionService
from app.services.audit_service import AuditService
from app.models.audit import AuditAction

router = APIRouter()


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Dependency to check if user has admin privileges."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


# ============== User Management ==============


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """List all users with optional filtering."""
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) | (User.username.ilike(f"%{search}%"))
        )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.offset(skip).limit(limit).all()
    return users


@router.post("/users", response_model=AdminUserResponse)
async def create_user(
    request: AdminUserCreate,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    req: Request,
):
    """Create a new user (admin only)."""
    auth_service_module = __import__("app.services.auth_service", fromlist=["AuthService"])
    AuthService = auth_service_module.AuthService
    
    auth_service = AuthService(db)
    audit_service = AuditService(db)
    
    # Check if email exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create user
    user = await auth_service.register_user(
        email=request.email,
        username=request.username,
        password=request.password,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user",
        )
    
    # Assign roles if provided
    if request.role_ids:
        role_service = RoleService(db)
        for role_id in request.role_ids:
            await role_service.assign_role_to_user(user.id, role_id)
    
    # Log action
    await audit_service.log_action(
        action=AuditAction.USER_CREATED,
        actor_user_id=admin.id,
        resource_type="user",
        resource_id=user.id,
        ip_address=req.client.host if req.client else None,
    )
    
    return user


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Get a specific user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: str,
    request: AdminUserUpdate,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    req: Request,
):
    """Update a user (admin only)."""
    audit_service = AuditService(db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if request.email:
        # Check if email is already taken
        existing = db.query(User).filter(User.email == request.email, User.id != user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        user.email = request.email
    
    if request.username:
        user.username = request.username
    
    if request.is_active is not None:
        user.is_active = request.is_active
    
    # Update roles if provided
    if request.role_ids is not None:
        role_service = RoleService(db)
        # Remove all existing roles
        from app.models.role import UserRole
        db.query(UserRole).filter(UserRole.user_id == user_id).delete()
        
        # Add new roles
        for role_id in request.role_ids:
            await role_service.assign_role_to_user(user_id, role_id)
    
    db.commit()
    db.refresh(user)
    
    # Log action
    await audit_service.log_action(
        action=AuditAction.USER_UPDATED,
        actor_user_id=admin.id,
        resource_type="user",
        resource_id=user_id,
        ip_address=req.client.host if req.client else None,
    )
    
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    req: Request,
):
    """Delete a user (admin only)."""
    audit_service = AuditService(db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Don't allow deleting yourself
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    
    db.delete(user)
    db.commit()
    
    # Log action
    await audit_service.log_action(
        action=AuditAction.USER_DELETED,
        actor_user_id=admin.id,
        resource_type="user",
        resource_id=user_id,
        ip_address=req.client.host if req.client else None,
    )
    
    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    req: Request,
):
    """Reset a user's password (admin only)."""
    from app.security.password import get_password_hash
    import secrets
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Generate temporary password
    temp_password = secrets.token_urlsafe(12)
    user.hashed_password = get_password_hash(temp_password)
    db.commit()
    
    # Log action
    audit_service = AuditService(db)
    await audit_service.log_action(
        action=AuditAction.PASSWORD_CHANGED,
        actor_user_id=admin.id,
        resource_type="user",
        resource_id=user_id,
        ip_address=req.client.host if req.client else None,
        metadata={"action": "admin_reset"},
    )
    
    return {
        "message": "Password reset successfully",
        "temporary_password": temp_password,
    }


# ============== Role Management ==============


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """List all roles."""
    role_service = RoleService(db)
    roles = await role_service.get_all_roles()
    return roles


@router.post("/roles", response_model=RoleResponse)
async def create_role(
    request: dict,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Create a new role."""
    role_service = RoleService(db)
    
    role = await role_service.create_role(
        name=request["name"],
        description=request.get("description", ""),
        permission_ids=request.get("permission_ids", []),
        is_default=request.get("is_default", False),
    )
    
    # Get full role with permissions
    all_roles = await role_service.get_all_roles()
    created_role = next((r for r in all_roles if r["id"] == role["id"]), None)
    
    return created_role


@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """List all available permissions."""
    permission_service = PermissionService(db)
    permissions = await permission_service.get_all_permissions()
    return permissions
