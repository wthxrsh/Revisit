from dataclasses import dataclass, field
from datetime import datetime

from secondbrain.clock import utc_now


@dataclass
class Note:
    id: int | None
    title: str
    content: str
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
