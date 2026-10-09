from dataclasses import dataclass, field
from datetime import datetime

from secondbrain.clock import utc_now


@dataclass
class Citation:
    document_id: int
    filename: str
    page_number: int | None
    chunk_id: int | None
    chunk_index: int
    snippet: str


@dataclass
class Message:
    role: str
    content: str
    id: int | None = None
    conversation_id: int | None = None
    citations: list[dict] | None = None
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Conversation:
    user_id: int
    title: str | None = None
    id: int | None = None
    created_at: datetime = field(default_factory=utc_now)
    messages: list[Message] = field(default_factory=list)
