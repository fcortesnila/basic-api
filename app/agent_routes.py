from fastapi import APIRouter

from app import agent_service
from app.agent_schemas import (
    AgentChatRequest,
    AgentChatResponse,
    AgentConfirmRequest,
    AgentConfirmResponse,
)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse, summary="Ask the directory agent")
def chat(request: AgentChatRequest) -> AgentChatResponse:
    """Answer directory questions and prepare changes for explicit confirmation."""
    return agent_service.chat(request.message)


@router.post("/confirm", response_model=AgentConfirmResponse, summary="Confirm a proposed change")
def confirm(request: AgentConfirmRequest) -> AgentConfirmResponse:
    """Apply one unexpired, single-use agent proposal."""
    action, user = agent_service.confirm_proposal(request.confirmation_id)
    return AgentConfirmResponse(action=action, user=user)
