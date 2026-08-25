"""
Database seeding script for initial data.
Creates default roles, permissions, and super admin user.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal, engine
from app.models.base import Base
from app.models.user import User
from app.models.role import Role, Permission, UserRole, RolePermission
from app.models.agent import Tool, RiskLevel
from app.security.password import get_password_hash
from app.core.config import settings


def create_default_permissions(db: Session) -> dict:
    """Create default permissions."""
    print("Creating default permissions...")
    
    default_permissions = [
        # User permissions
        ("users.view", "View users", "users", "view"),
        ("users.create", "Create users", "users", "create"),
        ("users.update", "Update users", "users", "update"),
        ("users.delete", "Delete users", "users", "delete"),
        
        # Role permissions
        ("roles.view", "View roles", "roles", "view"),
        ("roles.manage", "Manage roles", "roles", "manage"),
        
        # Chat permissions
        ("chat.access", "Access chat", "chat", "access"),
        ("chat.create", "Create conversations", "chat", "create"),
        ("chat.delete", "Delete conversations", "chat", "delete"),
        ("chat.history", "View chat history", "chat", "history"),
        
        # Agent permissions
        ("agent.access", "Access agent mode", "agent", "access"),
        ("agent.execute", "Execute agent tools", "agent", "execute"),
        ("agent.approve", "Approve agent actions", "agent", "approve"),
        
        # Model permissions
        ("models.view", "View models", "models", "view"),
        ("models.manage", "Manage models", "models", "manage"),
        
        # File permissions
        ("files.upload", "Upload files", "files", "upload"),
        ("files.download", "Download files", "files", "download"),
        ("files.delete", "Delete files", "files", "delete"),
        
        # Audit permissions
        ("audit.view", "View audit logs", "audit", "view"),
        
        # Settings permissions
        ("settings.view", "View settings", "settings", "view"),
        ("settings.manage", "Manage settings", "settings", "manage"),
    ]
    
    permissions_map = {}
    
    for name, description, resource, action in default_permissions:
        perm = Permission(
            name=name,
            description=description,
            resource=resource,
            action=action,
        )
        db.add(perm)
        permissions_map[name] = perm
    
    db.commit()
    
    return permissions_map


def create_default_roles(db: Session, permissions_map: dict) -> dict:
    """Create default roles with permissions."""
    print("Creating default roles...")
    
    roles_data = [
        (
            "SUPER_ADMIN",
            "Super Administrator - Full system access",
            True,
            list(permissions_map.keys()),  # All permissions
        ),
        (
            "ADMIN",
            "Administrator - User and system management",
            False,
            [
                "users.view", "users.create", "users.update",
                "roles.view",
                "chat.access", "chat.create", "chat.delete", "chat.history",
                "agent.access", "agent.execute", "agent.approve",
                "models.view",
                "files.upload", "files.download", "files.delete",
                "audit.view",
                "settings.view",
            ],
        ),
        (
            "AI_OPERATOR",
            "AI Operator - Advanced AI features",
            False,
            [
                "chat.access", "chat.create", "chat.delete", "chat.history",
                "agent.access", "agent.execute", "agent.approve",
                "models.view",
                "files.upload", "files.download",
            ],
        ),
        (
            "USER",
            "Standard User - Basic chat access",
            True,
            [
                "chat.access", "chat.create", "chat.history",
                "files.upload", "files.download",
            ],
        ),
    ]
    
    roles_map = {}
    
    for name, description, is_default, perm_names in roles_data:
        role = Role(
            name=name,
            description=description,
            is_default=is_default,
        )
        db.add(role)
        db.flush()
        
        roles_map[name] = role
        
        # Assign permissions
        for perm_name in perm_names:
            if perm_name in permissions_map:
                role_permission = RolePermission(
                    role_id=role.id,
                    permission_id=permissions_map[perm_name].id,
                )
                db.add(role_permission)
    
    db.commit()
    
    return roles_map


def create_super_admin(db: Session, roles_map: dict) -> User:
    """Create super admin user."""
    print("Creating super admin user...")
    
    email = settings.super_admin_email
    password = settings.super_admin_password
    
    # Check if already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"Super admin user already exists: {email}")
        return existing
    
    user = User(
        email=email,
        username="Administrator",
        hashed_password=get_password_hash(password),
        is_active=True,
        is_superuser=True,
    )
    
    db.add(user)
    db.flush()
    
    # Assign SUPER_ADMIN role
    if "SUPER_ADMIN" in roles_map:
        user_role = UserRole(
            user_id=user.id,
            role_id=roles_map["SUPER_ADMIN"].id,
        )
        db.add(user_role)
    
    db.commit()
    db.refresh(user)
    
    print(f"Super admin created: {email}")
    print("⚠️  IMPORTANT: Change the default password immediately!")
    
    return user


def create_default_tools(db: Session):
    """Create default agent tools."""
    print("Creating default tools...")
    
    tools_data = [
        (
            "calculator",
            "Calculator",
            "Perform mathematical calculations",
            {"type": "object", "properties": {"expression": {"type": "string", "description": "Math expression"}}, "required": ["expression"]},
            None,
            RiskLevel.LOW,
        ),
        (
            "datetime",
            "Date & Time",
            "Get current date and time information",
            {"type": "object", "properties": {"timezone": {"type": "string", "description": "Timezone"}}, "required": []},
            None,
            RiskLevel.LOW,
        ),
        (
            "web_search",
            "Web Search",
            "Search the web for information",
            {"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}}, "required": ["query"]},
            "agent.execute",
            RiskLevel.MEDIUM,
        ),
        (
            "fetch_url",
            "Fetch URL",
            "Fetch content from a URL",
            {"type": "object", "properties": {"url": {"type": "string", "description": "URL to fetch"}}, "required": ["url"]},
            "agent.execute",
            RiskLevel.MEDIUM,
        ),
        (
            "file_read",
            "Read File",
            "Read contents of a file",
            {"type": "object", "properties": {"path": {"type": "string", "description": "File path"}}, "required": ["path"]},
            "files.download",
            RiskLevel.MEDIUM,
        ),
        (
            "file_write",
            "Write File",
            "Write content to a file",
            {"type": "object", "properties": {"path": {"type": "string", "description": "File path"}, "content": {"type": "string", "description": "Content to write"}}, "required": ["path", "content"]},
            "files.upload",
            RiskLevel.HIGH,
        ),
    ]
    
    for name, display_name, description, schema_json, permission, risk_level in tools_data:
        tool = Tool(
            name=name,
            description=description,
            schema_json=schema_json,
            permission_required=permission,
            risk_level=risk_level,
            is_enabled=True,
        )
        db.add(tool)
    
    db.commit()
    print("Default tools created.")


def main():
    """Run database seeding."""
    print("=" * 50)
    print("AI Agent Workspace - Database Seeding")
    print("=" * 50)
    
    # Create tables
    print("\nCreating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = SessionLocal()
    
    try:
        # Create permissions
        permissions_map = create_default_permissions(db)
        print(f"✓ Created {len(permissions_map)} permissions")
        
        # Create roles
        roles_map = create_default_roles(db, permissions_map)
        print(f"✓ Created {len(roles_map)} roles")
        
        # Create super admin
        admin = create_super_admin(db, roles_map)
        
        # Create tools
        create_default_tools(db)
        
        print("\n" + "=" * 50)
        print("Seeding completed successfully!")
        print("=" * 50)
        print(f"\nLogin credentials:")
        print(f"  Email: {settings.super_admin_email}")
        print(f"  Password: {settings.super_admin_password}")
        print(f"\n⚠️  CHANGE THE DEFAULT PASSWORD IMMEDIATELY!\n")
        
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
