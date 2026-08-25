"""
Permission service for checking user permissions.
"""

from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Set


class PermissionService:
    """Service for managing and checking permissions."""

    def __init__(self, db: Session):
        self.db = db

    async def user_has_permission(self, user_id: str, permission_name: str) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user_id: The user's ID
            permission_name: The permission name (e.g., 'users.view')
            
        Returns:
            True if the user has the permission, False otherwise
        """
        from app.models.user import User
        from app.models.role import Role, Permission, UserRole, RolePermission
        
        # Superusers have all permissions
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
            
        if user.is_superuser:
            return True
        
        # Get all permissions through user's roles
        query = (
            select(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        
        result = self.db.execute(query)
        user_permissions: Set[str] = {row[0] for row in result.all()}
        
        return permission_name in user_permissions

    async def get_user_permissions(self, user_id: str) -> List[str]:
        """
        Get all permissions for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of permission names
        """
        from app.models.user import User
        from app.models.role import Role, Permission, UserRole, RolePermission
        
        # Superusers have all permissions
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
            
        if user.is_superuser:
            # Return all permissions
            all_perms = self.db.query(Permission).all()
            return [p.name for p in all_perms]
        
        # Get all permissions through user's roles
        query = (
            select(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        
        result = self.db.execute(query)
        return [row[0] for row in result.all()]

    async def get_all_permissions(self) -> List[dict]:
        """Get all available permissions."""
        from app.models.role import Permission
        
        permissions = self.db.query(Permission).order_by(Permission.resource, Permission.action).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "resource": p.resource,
                "action": p.action,
            }
            for p in permissions
        ]

    async def create_permission(self, name: str, description: str, resource: str, action: str) -> dict:
        """Create a new permission."""
        from app.models.role import Permission
        
        permission = Permission(
            name=name,
            description=description,
            resource=resource,
            action=action,
        )
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        
        return {
            "id": permission.id,
            "name": permission.name,
            "description": permission.description,
            "resource": permission.resource,
            "action": permission.action,
        }
