from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

SCHEMA_VERSION = 1


class EventType(str, Enum):
    swipe_right = 'swipe_right'
    swipe_left_style = 'swipe_left_style'
    swipe_left_price = 'swipe_left_price'
    save = 'save'
    open = 'open'
    edit_preference = 'edit_preference'


class InteractionEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    product_id: str
    event_type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    schema_version: int = SCHEMA_VERSION
