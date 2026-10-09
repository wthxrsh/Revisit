from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Note:
    id: int
    title: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)