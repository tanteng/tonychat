from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Message:
    """Message entity - represents a chat message"""
    role: str  # 'user' or 'assistant'
    content: str
    created_at: datetime
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }
