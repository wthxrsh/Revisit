from dataclasses import dataclass, field
from datetime import datetime

from secondbrain.clock import utc_now


@dataclass
class User:
    id: int | None
    email: str
    password_hash: str
    created_at: datetime = field(default_factory=utc_now)