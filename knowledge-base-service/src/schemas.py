from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class KBCreate(BaseModel):
    name: str
    visibility: str = "private"


class KBUpdate(BaseModel):
    name: Optional[str] = None
    visibility: Optional[str] = None


class KBOut(BaseModel):
    id: int
    name: str
    visibility: str
    owner_id: int

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: int
    kb_id: int
    title: str
    status: str
    metadata_json: dict[str, Any]

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    session_id: Optional[int] = None


class CitationOut(BaseModel):
    docName: str
    chunk: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationOut]
    usage: dict[str, Any]
    sessionId: int


class SessionOut(BaseModel):
    id: int
    kb_id: int
    user_id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    usage_json: dict[str, Any]

    class Config:
        from_attributes = True


class FeedbackIn(BaseModel):
    is_like: bool
    note: str = ""
