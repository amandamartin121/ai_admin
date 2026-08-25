"""
Role service for managing user roles.
"""

from sqlalchemy.orm import Session
from typing import List, Optional


class RoleService:
    """Service for managing roles."""

    def __init__(self, db: Session):
        self.db = db

    async def get_user_roles(self, user_id: str) -> List[dict]:
        """Get all roles for a user."""
        from app.models.role import Role, UserRole
        
        user_roles = (
            self.db.query(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user_id)
            .all()
        )
        
        return [
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_default": role.is_default,
            }
            for role in user_roles
        ]

    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """Assign a role to a user."""
        from app.models.role import UserRole, Role
        from app.models.user import User
        
        # Check if user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Check if role exists
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return False
        
        # Check if already assigned
        existing = (
            self.db.query(UserRole)
            .filter(UserRole.user_id == user_id, UserRole.role_id == role_id)
            .first()
        )
        if existing:
            return True  # Already assigned
        
        # Create assignment
        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.db.add(user_role)
        self.db.commit()
        
        return True

    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """Remove a role from a user."""
        from app.models.role import UserRole
        
        user_role = (
            self.db.query(UserRole)
            .filter(UserRole.user_id == user_id, UserRole.role_id == role_id)
            .first()
        )
        
        if not user_role:
            return False
        
        self.db.delete(user_role)
        self.db.commit()
        
        return True

    async def get_all_roles(self) -> List[dict]:
        """Get all roles with their permissions."""
        from app.models.role import Role, Permission, RolePermission
        
        roles = self.db.query(Role).order_by(Role.name).all()
        
        result = []
        for role in roles:
            permissions = (
                self.db.query(Permission)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .filter(RolePermission.role_id == role.id)
                .all()
            )
            
            result.append({
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_default": role.is_default,
                "permissions": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "resource": p.resource,
                        "action": p.action,
                    }
                    for p in permissions
                ],
            })
        
        return result

    async def create_role(
        self, name: str, description: str, permission_ids: List[str], is_default: bool = False
    ) -> dict:
        """Create a new role with permissions."""
        from app.models.role import Role, RolePermission
        
        role = Role(
            name=name,
            description=description,
            is_default=is_default,
        )
        self.db.add(role)
        self.db.flush()  # Get role ID
        
        # Assign permissions
        for perm_id in permission_ids:
            role_permission = RolePermission(role_id=role.id, permission_id=perm_id)
            self.db.add(role_permission)
        
        self.db.commit()
        self.db.refresh(role)
        
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_default": role.is_default,
        }

    async def update_role(
        self, role_id: str, name: Optional[str] = None, description: Optional[str] = None
    ) -> Optional[dict]:
        """Update a role."""
        from app.models.role import Role
        
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return None
        
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        
        self.db.commit()
        self.db.refresh(role)
        
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_default": role.is_default,
        }

    async def delete_role(self, role_id: str) -> bool:
        """Delete a role."""
        from app.models.role import Role
        
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return False
        
        # Don't allow deleting default roles
        if role.is_default:
            return False
        
        self.db.delete(role)
        self.db.commit()
        
        return True
