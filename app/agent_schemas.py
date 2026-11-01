from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas import User


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class AgentProposal(BaseModel):
    confirmation_id: str
    action: Literal["create", "update"]
    user_id: UUID | None = None
    changes: dict[str, str | None]
    expires_at: datetime


class AgentChatResponse(BaseModel):
    answer: str
    proposals: list[AgentProposal] = Field(default_factory=list)


class AgentConfirmRequest(BaseModel):
    confirmation_id: str = Field(min_length=32, max_length=128)


class AgentConfirmResponse(BaseModel):
    action: Literal["create", "update"]
    user: User
