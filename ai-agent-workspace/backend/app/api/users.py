"""
Users API routes for user management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from app.database.session import get_db
from app.schemas.auth import UserResponse, UserUpdate
from app.security.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user's profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    request: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update current user's profile."""
    if request.email:
        # Check if email is already taken
        existing = db.query(User).filter(User.email == request.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        current_user.email = request.email
    
    if request.username:
        current_user.username = request.username
    
    if request.is_active is not None and current_user.is_superuser:
        # Only superusers can change their own active status
        current_user.is_active = request.is_active
    
    db.commit()
    db.refresh(current_user)
    
    return current_user
