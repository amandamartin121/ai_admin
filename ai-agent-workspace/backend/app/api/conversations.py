"""
Conversations API routes for chat conversation management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from app.database.session import get_db
from app.security.dependencies import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, Message

router = APIRouter()


@router.get("", response_model=list[dict])
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = 0,
    limit: int = 50,
    archived: Optional[bool] = None,
):
    """List all conversations for the current user."""
    query = db.query(Conversation).filter(Conversation.user_id == current_user.id)
    
    if archived is not None:
        query = query.filter(Conversation.is_archived == archived)
    
    conversations = (
        query.order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return [
        {
            "id": c.id,
            "title": c.title,
            "mode": c.mode,
            "model_name": c.model_name,
            "is_archived": c.is_archived,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in conversations
    ]


@router.post("", response_model=dict)
async def create_conversation(
    request: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a new conversation."""
    conversation = Conversation(
        user_id=current_user.id,
        title=request.get("title", "New Conversation"),
        mode=request.get("mode", "chat"),
        model_name=request.get("model_name"),
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "mode": conversation.mode,
        "model_name": conversation.model_name,
        "is_archived": conversation.is_archived,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
    }


@router.get("/{conversation_id}", response_model=dict)
async def get_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get a specific conversation with its messages."""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    # Get messages
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "mode": conversation.mode,
        "model_name": conversation.model_name,
        "is_archived": conversation.is_archived,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "token_count": m.token_count,
                "created_at": m.created_at,
            }
            for m in messages
        ],
    }


@router.put("/{conversation_id}", response_model=dict)
async def update_conversation(
    conversation_id: str,
    request: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update a conversation."""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    if "title" in request:
        conversation.title = request["title"]
    
    if "mode" in request:
        conversation.mode = request["mode"]
    
    if "model_name" in request:
        conversation.model_name = request["model_name"]
    
    if "is_archived" in request:
        conversation.is_archived = request["is_archived"]
    
    db.commit()
    db.refresh(conversation)
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "mode": conversation.mode,
        "model_name": conversation.model_name,
        "is_archived": conversation.is_archived,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
    }


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete a conversation."""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    db.delete(conversation)
    db.commit()
    
    return {"message": "Conversation deleted successfully"}


@router.post("/{conversation_id}/messages", response_model=dict)
async def create_message(
    conversation_id: str,
    request: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Add a message to a conversation."""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    message = Message(
        conversation_id=conversation_id,
        role=request["role"],
        content=request["content"],
        token_count=request.get("token_count"),
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Update conversation updated_at
    conversation.updated_at = db.func.now()
    db.commit()
    
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at,
    }
