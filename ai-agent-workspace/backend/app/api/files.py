"""
Files API routes for file upload and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Annotated, Optional
import os
import hashlib
import uuid
from pathlib import Path
from datetime import datetime, timezone

from app.database.session import get_db
from app.security.dependencies import get_current_user
from app.models.user import User
from app.models.file import File as FileModel
from app.core.config import settings
from app.services.audit_service import AuditService
from app.models.audit import AuditAction

router = APIRouter()


ALLOWED_MIME_TYPES = {
    "text/plain": [".txt", ".md", ".csv", ".json"],
    "application/pdf": [".pdf"],
    "application/json": [".json"],
    "text/markdown": [".md"],
    "text/csv": [".csv"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
}

ALLOWED_EXTENSIONS = {ext for exts in ALLOWED_MIME_TYPES.values() for ext in exts}


def validate_file(file: UploadFile) -> tuple[str, str]:
    """Validate file type and return extension and validated MIME type."""
    # Get file extension
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()
    
    if not ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have an extension",
        )
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {ext} not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    
    # Validate MIME type
    content_type = file.content_type or "application/octet-stream"
    
    if content_type not in ALLOWED_MIME_TYPES:
        # Allow if extension matches a known type
        valid = any(ext in exts for exts in ALLOWED_MIME_TYPES.values() if ext == ext)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content type {content_type} not allowed",
            )
    
    return ext, content_type


@router.post("/upload", response_model=dict)
async def upload_file(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    req: Request,
):
    """Upload a file."""
    permission_service_module = __import__("app.services.permission_service", fromlist=["PermissionService"])
    PermissionService = permission_service_module.PermissionService
    
    permission_service = PermissionService(db)
    audit_service = AuditService(db)
    
    # Check permission
    has_upload_permission = await permission_service.user_has_permission(
        current_user.id, "files.upload"
    )
    
    if not has_upload_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="File upload permission denied",
        )
    
    # Validate file
    ext, content_type = validate_file(file)
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Check file size
    if file_size > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.max_upload_size} bytes",
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}{ext}"
    
    # Create storage directory if needed
    storage_path = Path(settings.file_storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = storage_path / safe_filename
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Calculate checksum
    checksum = hashlib.sha256(content).hexdigest()
    
    # Create database record
    db_file = FileModel(
        user_id=current_user.id,
        filename=safe_filename,
        original_filename=file.filename or "uploaded_file",
        mime_type=content_type,
        file_size=file_size,
        file_path=str(file_path.relative_to(storage_path)) if file_path.is_relative_to(storage_path) else str(file_path),
        checksum=checksum,
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # Log action
    await audit_service.log_action(
        action=AuditAction.FILE_UPLOADED,
        actor_user_id=current_user.id,
        resource_type="file",
        resource_id=db_file.id,
        ip_address=req.client.host if req.client else None,
        metadata={"filename": file.filename, "size": file_size},
    )
    
    return {
        "id": db_file.id,
        "filename": db_file.original_filename,
        "mime_type": db_file.mime_type,
        "file_size": db_file.file_size,
        "created_at": db_file.created_at,
    }


@router.get("", response_model=list[dict])
async def list_files(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = 0,
    limit: int = 50,
):
    """List all files for the current user."""
    files = (
        db.query(FileModel)
        .filter(FileModel.user_id == current_user.id)
        .order_by(FileModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return [
        {
            "id": f.id,
            "filename": f.original_filename,
            "mime_type": f.mime_type,
            "file_size": f.file_size,
            "created_at": f.created_at,
        }
        for f in files
    ]


@router.get("/{file_id}", response_model=dict)
async def get_file(
    file_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get file metadata."""
    file = (
        db.query(FileModel)
        .filter(FileModel.id == file_id, FileModel.user_id == current_user.id)
        .first()
    )
    
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    return {
        "id": file.id,
        "filename": file.original_filename,
        "mime_type": file.mime_type,
        "file_size": file.file_size,
        "checksum": file.checksum,
        "created_at": file.created_at,
    }


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Download a file."""
    file = (
        db.query(FileModel)
        .filter(FileModel.id == file_id, FileModel.user_id == current_user.id)
        .first()
    )
    
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    # Construct full path
    storage_path = Path(settings.file_storage_path)
    file_path = storage_path / file.filename
    
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")
    
    # Log download
    audit_service = AuditService(db)
    await audit_service.log_action(
        action=AuditAction.FILE_DOWNLOADED,
        actor_user_id=current_user.id,
        resource_type="file",
        resource_id=file_id,
    )
    
    return FileResponse(
        path=str(file_path),
        media_type=file.mime_type,
        filename=file.original_filename,
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    req: Request,
):
    """Delete a file."""
    audit_service = AuditService(db)
    
    file = (
        db.query(FileModel)
        .filter(FileModel.id == file_id, FileModel.user_id == current_user.id)
        .first()
    )
    
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    # Delete from disk
    storage_path = Path(settings.file_storage_path)
    file_path = storage_path / file.filename
    
    if file_path.exists():
        os.remove(str(file_path))
    
    # Delete from database
    db.delete(file)
    db.commit()
    
    # Log action
    await audit_service.log_action(
        action=AuditAction.FILE_DELETED,
        actor_user_id=current_user.id,
        resource_type="file",
        resource_id=file_id,
        ip_address=req.client.host if req.client else None,
    )
    
    return {"message": "File deleted successfully"}
