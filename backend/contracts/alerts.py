from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

SCHEMA_VERSION = 1

FREE_ALERT_LIMIT = 3


class AlertType(str, Enum):
    specific_item = "specific_item"
    style = "style"


class AlertStatus(str, Enum):
    active = "active"
    paused = "paused"


class AlertConstraints(BaseModel):
    max_price_eur: float | None = None
    sizes: list[str] = Field(default_factory=list)
    min_condition: str | None = None


class Alert(BaseModel):
    alert_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    alert_type: AlertType
    label: str
    reference_embedding: list[float] | None = None
    reference_product_id: str | None = None
    constraints: AlertConstraints = Field(default_factory=AlertConstraints)
    status: AlertStatus = AlertStatus.active
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    schema_version: int = SCHEMA_VERSION
