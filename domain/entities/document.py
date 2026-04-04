from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Document:
    """Document entity - represents an uploaded document"""
    id: str
    filename: str
    file_path: str
    content: str
    file_type: str
    uploaded_at: datetime
    chunk_count: int = 0

    @property
    def is_empty(self) -> bool:
        return len(self.content.strip()) == 0

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'uploaded_at': self.uploaded_at.isoformat(),
            'chunk_count': self.chunk_count
        }
