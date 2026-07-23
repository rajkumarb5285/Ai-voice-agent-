from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# ─── Auth ────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    profile: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[str] = None


# ─── Chat ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    mode: str = "chat"  # chat | voice
    stream: bool = True


class ChatMessage(BaseModel):
    role: str
    content: str
    agent_name: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    created_at: Optional[datetime] = None


class ConversationResponse(BaseModel):
    id: UUID
    title: Optional[str]
    mode: str
    messages: List[ChatMessage] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Memory ──────────────────────────────────────────────────────────────────

class MemoryCreate(BaseModel):
    memory_type: str
    category: Optional[str] = None
    title: Optional[str] = None
    content: str
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata_: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")


class MemoryResponse(BaseModel):
    id: UUID
    memory_type: str
    category: Optional[str]
    title: Optional[str]
    content: str
    importance_score: float
    created_at: datetime
    accessed_at: Optional[datetime]

    class Config:
        from_attributes = True


class MemorySearchRequest(BaseModel):
    query: str
    n_results: int = Field(default=5, ge=1, le=20)
    memory_types: Optional[List[str]] = None


# ─── Tasks ───────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    category: Optional[str] = None
    due_date: Optional[datetime] = None
    steps: Optional[List[Dict]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    steps: Optional[List[Dict]] = None


class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    status: str
    priority: str
    category: Optional[str]
    steps: Optional[List[Dict]]
    due_date: Optional[datetime]
    is_ai_generated: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Voice ───────────────────────────────────────────────────────────────────

class TranscriptionResponse(BaseModel):
    text: str
    confidence: Optional[float] = None
    language: Optional[str] = None
    duration_seconds: Optional[float] = None


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    provider: Optional[str] = None  # openai | elevenlabs


# ─── Agent Activity ──────────────────────────────────────────────────────────

class AgentActivity(BaseModel):
    agent_name: str
    action: str
    status: str  # running | completed | error
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    duration_ms: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StreamChunk(BaseModel):
    type: str  # text | agent_activity | audio | done | error
    content: Optional[str] = None
    agent_activity: Optional[AgentActivity] = None
    metadata: Optional[Dict[str, Any]] = None
