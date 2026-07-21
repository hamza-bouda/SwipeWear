"""Tests for preferences.updater -- PreferenceUpdater (KAN-32)."""
from __future__ import annotations

import math
from datetime import datetime, timezone
from uuid import UUID

import pytest

from contracts.events import EventType, InteractionEvent
from contracts.profile import HardConstraints, StyleVectors, UserPreferenceProfile
from preferences.config import ALPHA, ALPHA_STRONG, BETA, PRICE_DISCOUNT
from preferences.updater import PreferenceUpdater

USER_ID = UUID("00000000-0000-0000-0000-000000000042")
T0 = datetime(2026, 7, 21, 10, 0, 0, tzinfo=timezone.utc)
EMBEDDING = [1.0] + [0.0] * 511


def _event(event_type: EventType, **payload) -> InteractionEvent:
    return InteractionEvent(
        user_id=USER_ID,
        product_id="p1",
        event_type=event_type,
        payload=payload,
        timestamp=T0,
    )


def _profile(**overrides) -> UserPreferenceProfile:
    defaults: dict = dict(user_id=USER_ID)
    defaults.update(overrides)
    return UserPreferenceProfile(**defaults)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


class TestSwipeRight:
    def test_moves_positive_vector_toward_embedding(self) -> None:
        updated = PreferenceUpdater().apply(
            _profile(), _event(EventType.swipe_right, product_embedding=EMBEDDING),
        )
        assert _cosine(updated.vectors.positive, EMBEDDING) == pytest.approx(1.0)

    def test_does_not_touch_negative_vector(self) -> None:
        updated = PreferenceUpdater().apply(
            _profile(), _event(EventType.swipe_right, product_embedding=EMBEDDING),
        )
        assert updated.vectors.negative == []

    def test_adds_brand_to_liked_brands(self) -> None:
        updated = PreferenceUpdater().apply(
            _profile(),
            _event(EventType.swipe_right, product_embedding=EMBEDDING, brand="Carhartt"),
        )
        assert "Carhartt" in updated.editable_preferences.liked_brands

    def test_increments_event_count(self) -> None:
        updated = PreferenceUpdater().apply(
            _profile(), _event(EventType.swipe_right, product_embedding=EMBEDDING),
        )
        assert updated.event_count == 1

    def test_no_embedding_in_payload_is_a_no_op_on_vectors(self) -> None:
        updated = PreferenceUpdater().apply(_profile(), _event(EventType.swipe_right))
        assert updated.vectors.positive == []


class TestSwipeLeftStyle:
    def test_moves_negative_vector_toward_embedding(self) -> None:
        updated = PreferenceUpdater().apply(
            _profile(), _event(EventType.swipe_left_style, product_embedding=EMBEDDING),
        )
        assert _cosine(updated.vectors.negative, EMBEDDING) == pytest.approx(1.0)

    def test_does_not_touch_positive_vector(self) -> None:
        updated = PreferenceUpdater().apply(
            _profile(), _event(EventType.swipe_left_style, product_embedding=EMBEDDING),
        )
        assert updated.vectors.positive == []


class TestSwipeLeftPrice:
    def test_sets_discounted_max_price(self) -> None:
        updated = PreferenceUpdater().apply(
            _profile(), _event(EventType.swipe_left_price, product_price_eur=100.0),
        )
        assert updated.hard_constraints.max_price_eur == pytest.approx(90.0)

    def test_only_lowers_never_raises_budget(self) -> None:
        profile = _profile(hard_constraints=HardConstraints(max_price_eur=50.0))
        updated = PreferenceUpdater().apply(
            profile, _event(EventType.swipe_left_price, product_price_eur=1000.0),
        )
        assert updated.hard_constraints.max_price_eur == 50.0

    def test_style_vectors_strictly_unchanged(self) -> None:
        """AC critique: un swipe_left_price ne touche JAMAIS le vecteur de style."""
        profile = _profile(
            vectors=StyleVectors(positive=[0.3] * 512, negative=[0.1] * 512),
        )
        updated = PreferenceUpdater().apply(
            profile, _event(EventType.swipe_left_price, product_price_eur=10.0),
        )
        assert updated.vectors.positive == profile.vectors.positive
        assert updated.vectors.negative == profile.vectors.negative


class TestSaveAndOpen:
    @pytest.mark.parametrize("event_type", [EventType.save, EventType.open])
    def test_moves_positive_vector_toward_embedding(self, event_type) -> None:
        updated = PreferenceUpdater().apply(
            _profile(), _event(event_type, product_embedding=EMBEDDING),
        )
        assert _cosine(updated.vectors.positive, EMBEDDING) == pytest.approx(1.0)

    def test_alpha_strong_is_double_alpha(self) -> None:
        assert ALPHA_STRONG == pytest.approx(ALPHA * 2)


class TestEditPreference:
    def test_liked_brand_added(self) -> None:
        updated = PreferenceUpdater().apply(
            _profile(),
            _event(EventType.edit_preference, field="liked_brands", value="Nike"),
        )
        assert "Nike" in updated.editable_preferences.liked_brands

    def test_rejected_brand_added(self) -> None:
        updated = PreferenceUpdater().apply(
            _profile(),
            _event(EventType.edit_preference, field="rejected_brands", value="Shein"),
        )
        assert "Shein" in updated.editable_preferences.rejected_brands

    def test_max_price_direct_override_no_discount(self) -> None:
        updated = PreferenceUpdater().apply(
            _profile(),
            _event(EventType.edit_preference, field="max_price_eur", value=42.0),
        )
        assert updated.hard_constraints.max_price_eur == 42.0

    def test_does_not_touch_style_vectors(self) -> None:
        profile = _profile(vectors=StyleVectors(positive=[0.5] * 512))
        updated = PreferenceUpdater().apply(
            profile,
            _event(EventType.edit_preference, field="liked_brands", value="Nike"),
        )
        assert updated.vectors.positive == profile.vectors.positive


class TestConfigIsUsedNotHardcoded:
    def test_constants_are_floats(self) -> None:
        assert isinstance(ALPHA, float)
        assert isinstance(BETA, float)
        assert isinstance(PRICE_DISCOUNT, float)
