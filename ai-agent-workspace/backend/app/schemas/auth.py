"""
Pydantic schemas for authentication and user management.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ============== Authentication Schemas ==============


class Token(BaseModel):
    """Token response containing access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Payload decoded from JWT token."""

    sub: str  # User ID
    exp: datetime
    type: str  # 'access' or 'refresh'


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    """User registration request schema."""

    email: EmailStr
    username: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)


class ChangePasswordRequest(BaseModel):
    """Password change request schema."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


# ============== User Schemas ==============


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr
    username: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a user (admin only)."""

    password: str = Field(..., min_length=8, max_length=100)
    is_active: bool = True
    is_superuser: bool = False


class UserUpdate(BaseModel):
    """Schema for updating user fields."""

    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response data."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UserInDB(UserBase):
    """Internal schema for user in database."""

    id: str
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ============== Session Schemas ==============


class SessionResponse(BaseModel):
    """Schema for session information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    last_used_at: Optional[datetime] = None
    created_at: datetime


class SessionList(BaseModel):
    """Schema for listing sessions."""

    sessions: List[SessionResponse]
    total: int


# ============== Role & Permission Schemas ==============


class PermissionBase(BaseModel):
    """Base permission schema."""

    name: str
    description: Optional[str] = None
    resource: str
    action: str


class PermissionResponse(PermissionBase):
    """Permission response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class RoleBase(BaseModel):
    """Base role schema."""

    name: str
    description: Optional[str] = None


class RoleResponse(RoleBase):
    """Role response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    is_default: bool
    permissions: List[PermissionResponse] = []
    created_at: datetime
    updated_at: datetime


class RoleCreate(RoleBase):
    """Schema for creating a role."""

    permission_ids: List[str] = []


class RoleUpdate(BaseModel):
    """Schema for updating a role."""

    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[str]] = None


# ============== Admin Schemas ==============


class AdminUserCreate(UserCreate):
    """Admin schema for creating users with roles."""

    role_ids: List[str] = []


class AdminUserUpdate(UserUpdate):
    """Admin schema for updating users with roles."""

    role_ids: Optional[List[str]] = None


class AdminUserResponse(UserResponse):
    """Admin schema for user response with roles."""

    roles: List[RoleResponse] = []
