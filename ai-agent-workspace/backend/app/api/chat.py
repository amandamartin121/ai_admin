"""
Chat API routes for AI chat completions with streaming support.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Annotated, Optional
import json
import asyncio

from app.database.session import get_db
from app.security.dependencies import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.core.config import settings

router = APIRouter()


async def generate_stream(
    messages: list[dict],
    model: str,
):
    """Generate streaming response from LLM."""
    # Check if we have an OpenAI API key
    if not settings.openai_api_key:
        # Return mock response for development without API key
        yield "data: " + json.dumps({"type": "message_start"}) + "\n\n"
        
        mock_response = "Hello! I'm the AI assistant. Since no API key is configured, this is a mock response. Please configure your OpenAI API key in the environment variables to get real AI responses."
        
        for word in mock_response.split():
            await asyncio.sleep(0.05)  # Simulate streaming delay
            yield "data: " + json.dumps({"type": "token", "content": word + " "}) + "\n\n"
        
        yield "data: " + json.dumps({"type": "message_end", "usage": {"prompt_tokens": 10, "completion_tokens": 30, "total_tokens": 40}}) + "\n\n"
        yield "data: [DONE]\n\n"
        return
    
    # Real OpenAI-compatible streaming
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{settings.openai_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            yield "data: [DONE]\n\n"
                        else:
                            yield f"data: {data}\n\n"
    
    except Exception as e:
        yield "data: " + json.dumps({"type": "error", "message": str(e)}) + "\n\n"
        yield "data: [DONE]\n\n"


@router.post("/completions")
async def create_chat_completion(
    request: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a chat completion with optional streaming."""
    conversation_id = request.get("conversation_id")
    messages = request.get("messages", [])
    model = request.get("model", settings.default_model)
    stream = request.get("stream", True)
    
    # Validate messages
    if not messages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Messages required")
    
    # Check permission for agent mode
    mode = request.get("mode", "chat")
    if mode == "agent":
        # Check if user has agent.access permission
        from app.services.permission_service import PermissionService
        permission_service = PermissionService(db)
        has_agent_access = await permission_service.user_has_permission(
            current_user.id, "agent.access"
        )
        
        if not has_agent_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent mode access denied. Contact an administrator.",
            )
    
    # Create or get conversation
    if conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
            .first()
        )
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    else:
        conversation = Conversation(
            user_id=current_user.id,
            title=messages[0].get("content", "New Conversation")[:50],
            mode=mode,
            model_name=model,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conversation_id = conversation.id
    
    # Save user message
    user_message = messages[-1] if messages else None
    if user_message and user_message.get("role") == "user":
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=user_message.get("content", ""),
        )
        db.add(user_msg)
        db.commit()
    
    if stream:
        return StreamingResponse(
            generate_stream(messages, model),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # Non-streaming response (simplified for now)
        return {
            "id": conversation_id,
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Non-streaming mode not fully implemented yet.",
                    }
                }
            ],
        }


@router.post("/stop/{conversation_id}")
async def stop_generation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Stop an ongoing generation (placeholder for future implementation)."""
    # In a real implementation, this would signal the streaming task to stop
    # For now, just validate the conversation exists
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    return {"message": "Stop signal sent"}
