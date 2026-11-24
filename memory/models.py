from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class MemoryCategory(str, Enum):
    PERSONAL = "personal"
    PROJECT = "project"
    PROFESSIONAL = "professional"
    EDUCATION = "education"
    PREFERENCE = "preference"
    GENERAL = "general"


def current_timestamp():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Memory:

    content: str
    category: MemoryCategory = MemoryCategory.GENERAL

    memory_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    source: str = "conversation"
    source_conversation_id: str | None = None

    importance: float = 0.5
    confidence: float = 1.0

    created_at: str = field(
        default_factory=current_timestamp
    )

    updated_at: str = field(
        default_factory=current_timestamp
    )

    last_accessed_at: str | None = None

    metadata: dict = field(default_factory=dict)

    def __post_init__(self):

        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("Memory content cannot be empty.")

        if isinstance(self.category, str):
            self.category = MemoryCategory(self.category)

        if not 0.0 <= self.importance <= 1.0:
            raise ValueError(
                "Importance must be between 0.0 and 1.0."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Confidence must be between 0.0 and 1.0."
            )

        if not isinstance(self.metadata, dict):
            raise ValueError("Memory metadata must be a dictionary.")

    def to_dict(self):

        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "category": self.category.value,
            "source": self.source,
            "source_conversation_id": self.source_conversation_id,
            "importance": self.importance,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_accessed_at": self.last_accessed_at,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data):

        return cls(
            memory_id=data["memory_id"],
            content=data["content"],
            category=MemoryCategory(data["category"]),
            source=data["source"],
            source_conversation_id=data.get(
                "source_conversation_id"
            ),
            importance=data["importance"],
            confidence=data["confidence"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            last_accessed_at=data.get("last_accessed_at"),
            metadata=data.get("metadata", {})
        )