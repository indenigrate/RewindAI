from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class StoredEvent:
    event_number: int
    event_id: UUID
    event_type: str
    payload: Dict[str, Any]
    thread_id: str
    parent_event_id: Optional[UUID] = None  # ✅ DEFAULT
    created_at: datetime = None
