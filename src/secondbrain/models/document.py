from dataclasses import dataclass, field
from datetime import datetime

from secondbrain.clock import utc_now


class DocumentStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Document:
    user_id: int
    original_filename: str
    storage_key: str
    file_size: int
    mime_type: str
    status: str = DocumentStatus.PENDING
    id: int | None = None
    error_message: str | None = None
    page_count: int | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    processed_at: datetime | None = None

    @property
    def is_processable(self) -> bool:
        return self.status != DocumentStatus.PROCESSING
