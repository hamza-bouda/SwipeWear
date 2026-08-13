
import json
from uuid import UUID

import pytest

from contracts.events import EventType, InteractionEvent

USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def make_event(**kwargs) -> InteractionEvent:
    defaults = {
        "user_id": USER_ID,
        "product_id": "prod-001",
        "event_type": EventType.swipe_right,
    }
    return InteractionEvent(**{**defaults, **kwargs})


class TestInteractionEventSchema:
    def test_valid_event_creates_successfully(self):
        event = make_event()
        assert isinstance(event.event_id, UUID)
        assert event.schema_version == 1
        assert event.event_type == EventType.swipe_right

    def test_all_event_types_are_valid(self):
        for et in EventType:
            event = make_event(event_type=et)
            assert event.event_type == et

    def test_payload_defaults_to_empty_dict(self):
        event = make_event()
        assert event.payload == {}

    def test_payload_accepts_arbitrary_data(self):
        event = make_event(
            event_type=EventType.edit_preference,
            payload={"field": "liked_brands", "value": "Nike"},
        )
        assert event.payload["field"] == "liked_brands"

    def test_serialization_roundtrip(self):
        event = make_event(payload={"product_price_eur": 49.99})
        restored = InteractionEvent.model_validate_json(event.model_dump_json())
        assert restored == event

    def test_json_is_valid_json(self):
        event = make_event()
        parsed = json.loads(event.model_dump_json())
        assert parsed["schema_version"] == 1
        assert "event_id" in parsed
        assert "timestamp" in parsed
