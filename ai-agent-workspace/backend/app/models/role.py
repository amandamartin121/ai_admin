"""
Role and Permission models for RBAC system.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class Role(Base, PrimaryKeyMixin, TimestampMixin):
    """
    Role model representing user roles in the system.
    
    Roles group permissions together for easier assignment to users.
    """

    __tablename__ = "roles"

    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)

    # Relationships
    permissions = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )
    users = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(Base, PrimaryKeyMixin, TimestampMixin):
    """
    Permission model representing granular access rights.
    
    Permissions define specific actions that can be performed on resources.
    """

    __tablename__ = "permissions"

    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    resource = Column(String(50), nullable=False)  # e.g., 'users', 'chat', 'agent'
    action = Column(String(50), nullable=False)  # e.g., 'view', 'create', 'execute'

    # Relationships
    roles = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_permissions_resource", "resource"),
        Index("ix_permissions_action", "action"),
        UniqueConstraint("resource", "action", name="uq_resource_action"),
    )

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name={self.name})>"


class UserRole(Base, PrimaryKeyMixin, TimestampMixin):
    """
    Association table linking users to roles.
    """

    __tablename__ = "user_roles"

    user_id = Column(PG_UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(PG_UUID(as_uuid=False), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
        Index("ix_user_roles_user_id", "user_id"),
        Index("ix_user_roles_role_id", "role_id"),
    )

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class RolePermission(Base, PrimaryKeyMixin, TimestampMixin):
    """
    Association table linking roles to permissions.
    """

    __tablename__ = "role_permissions"

    role_id = Column(PG_UUID(as_uuid=False), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(
        String(36), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")

    # Constraints
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
        Index("ix_role_permissions_role_id", "role_id"),
        Index("ix_role_permissions_permission_id", "permission_id"),
    )

    def __repr__(self) -> str:
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"
