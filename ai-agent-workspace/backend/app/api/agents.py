"""
Agents API routes for agentic AI execution.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import datetime, timezone, timedelta

from app.database.session import get_db
from app.security.dependencies import get_current_user
from app.models.user import User
from app.models.agent import AgentRun, AgentStep, AgentStatus, Tool, RiskLevel
from app.models.approval import ApprovalRequest, ApprovalStatus
from app.services.permission_service import PermissionService
from app.services.audit_service import AuditService
from app.models.audit import AuditAction

router = APIRouter()


@router.post("/run", response_model=dict)
async def start_agent_run(
    request: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Start a new agent run."""
    permission_service = PermissionService(db)
    audit_service = AuditService(db)
    
    # Check if user has agent.access permission
    has_agent_access = await permission_service.user_has_permission(
        current_user.id, "agent.access"
    )
    
    if not has_agent_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent mode access denied. Contact an administrator.",
        )
    
    conversation_id = request.get("conversation_id")
    user_request = request.get("request", "")
    
    if not user_request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request required")
    
    # Create agent run
    agent_run = AgentRun(
        conversation_id=conversation_id,
        user_request=user_request,
        status=AgentStatus.PLANNING,
        current_step=0,
    )
    
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)
    
    # Log action
    await audit_service.log_action(
        action=AuditAction.AGENT_STARTED,
        actor_user_id=current_user.id,
        resource_type="agent_run",
        resource_id=agent_run.id,
        metadata={"user_request": user_request[:100]},
    )
    
    return {
        "id": agent_run.id,
        "status": agent_run.status.value,
        "current_step": agent_run.current_step,
        "created_at": agent_run.created_at,
    }


@router.get("/runs/{run_id}", response_model=dict)
async def get_agent_run(
    run_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get agent run status and steps."""
    from app.models.conversation import Conversation
    
    # Verify ownership through conversation
    run = (
        db.query(AgentRun)
        .join(Conversation, Conversation.id == AgentRun.conversation_id)
        .filter(AgentRun.id == run_id, Conversation.user_id == current_user.id)
        .first()
    )
    
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    
    # Get steps
    steps = (
        db.query(AgentStep)
        .filter(AgentStep.run_id == run_id)
        .order_by(AgentStep.step_number)
        .all()
    )
    
    return {
        "id": run.id,
        "status": run.status.value,
        "current_step": run.current_step,
        "total_steps": run.total_steps,
        "result": run.result,
        "error_message": run.error_message,
        "steps": [
            {
                "id": step.id,
                "step_number": step.step_number,
                "step_type": step.step_type,
                "description": step.description,
                "tool_input": step.tool_input,
                "tool_output": step.tool_output,
                "status": step.status,
                "duration_ms": step.duration_ms,
            }
            for step in steps
        ],
    }


@router.get("/approvals/pending", response_model=list[dict])
async def get_pending_approvals(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get pending approval requests for the user."""
    approvals = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.user_id == current_user.id,
            ApprovalRequest.status == ApprovalStatus.PENDING,
            ApprovalRequest.expires_at > datetime.now(timezone.utc),
        )
        .all()
    )
    
    return [
        {
            "id": approval.id,
            "run_id": approval.run_id,
            "tool_id": approval.tool_id,
            "action_description": approval.action_description,
            "risk_level": approval.risk_level,
            "expires_at": approval.expires_at,
            "created_at": approval.created_at,
        }
        for approval in approvals
    ]


@router.post("/approvals/{approval_id}/approve", response_model=dict)
async def approve_action(
    approval_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Approve a pending agent action."""
    permission_service = PermissionService(db)
    audit_service = AuditService(db)
    
    # Check if user has agent.approve permission
    has_approve_permission = await permission_service.user_has_permission(
        current_user.id, "agent.approve"
    )
    
    approval = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.id == approval_id,
            ApprovalRequest.user_id == current_user.id,
            ApprovalRequest.status == ApprovalStatus.PENDING,
        )
        .first()
    )
    
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")
    
    if approval.expires_at < datetime.now(timezone.utc):
        approval.status = ApprovalStatus.EXPIRED
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Approval request expired")
    
    # Update approval
    approval.status = ApprovalStatus.APPROVED
    approval.approved_by = current_user.id
    approval.approved_at = datetime.now(timezone.utc)
    db.commit()
    
    # Log action
    await audit_service.log_action(
        action=AuditAction.APPROVAL_APPROVED,
        actor_user_id=current_user.id,
        resource_type="approval_request",
        resource_id=approval_id,
    )
    
    return {"message": "Action approved"}


@router.post("/approvals/{approval_id}/reject", response_model=dict)
async def reject_action(
    approval_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Reject a pending agent action."""
    audit_service = AuditService(db)
    
    approval = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.id == approval_id,
            ApprovalRequest.user_id == current_user.id,
            ApprovalRequest.status == ApprovalStatus.PENDING,
        )
        .first()
    )
    
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")
    
    # Update approval
    approval.status = ApprovalStatus.REJECTED
    db.commit()
    
    # Log action
    await audit_service.log_action(
        action=AuditAction.APPROVAL_REJECTED,
        actor_user_id=current_user.id,
        resource_type="approval_request",
        resource_id=approval_id,
    )
    
    return {"message": "Action rejected"}


@router.get("/tools", response_model=list[dict])
async def list_tools(
    db: Annotated[Session, Depends(get_db)],
):
    """List available tools."""
    tools = db.query(Tool).filter(Tool.is_enabled == True).all()
    
    return [
        {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "schema": tool.schema_json,
            "risk_level": tool.risk_level.value,
            "permission_required": tool.permission_required,
        }
        for tool in tools
    ]
