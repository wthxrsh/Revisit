from dataclasses import dataclass, field
from datetime import datetime

from secondbrain.clock import utc_now


@dataclass
class Chunk:
    chunk_index: int
    content: str
    page_number: int | None = None
    page_end: int | None = None
    id: int | None = None
    document_id: int | None = None
    user_id: int | None = None
    embedding: list[float] | None = None
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class ScoredChunk:
    chunk: Chunk
    score: float
    document_id: int
    filename: str
