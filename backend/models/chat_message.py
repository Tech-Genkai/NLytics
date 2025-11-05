"""
Chat Message Model
Represents different types of messages in the chat interface
"""
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime


class MessageType(Enum):
    """Types of chat messages"""
    USER = "user"
    SYSTEM = "system"
    ERROR = "error"
    PROGRESS = "progress"
    RESULT = "result"
    CLARIFICATION = "clarification"


@dataclass
class ChatMessage:
    """
    Represents a single message in the chat interface
    """
    type: MessageType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'type': self.type.value,
            'content': self.content,
            'metadata': self.metadata or {},
            'timestamp': self.metadata.get('timestamp', datetime.utcnow().isoformat()) if self.metadata else datetime.utcnow().isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create ChatMessage from dictionary"""
        return cls(
            type=MessageType(data['type']),
            content=data['content'],
            metadata=data.get('metadata')
        )
