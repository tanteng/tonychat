from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class ChatRequest:
    """DTO for chat request"""
    message: str
    model: str = "openai"


@dataclass
class ChatResponse:
    """DTO for chat response"""
    content: str
    sources: Optional[List[str]] = None


@dataclass
class DocumentDTO:
    """DTO for document representation"""
    id: str
    filename: str
    file_type: str
    uploaded_at: str
    chunk_count: int = 0
