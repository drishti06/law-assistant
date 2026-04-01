from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(default="en", pattern="^(en|hi)$")


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatSession(BaseModel):
    user_email: str
    messages: list[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatResponse(BaseModel):
    answer: str
    short_answer: str
    explanation: str
    relevant_law: str
    next_steps: str
    disclaimer: str
    sources: list[str] = []


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatMessage]
    created_at: datetime
    updated_at: datetime


class DocumentUpload(BaseModel):
    title: str
    content: str
    category: Optional[str] = "general"
