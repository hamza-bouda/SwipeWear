import json
from datetime import datetime, timezone
from uuid import UUID

import pytest

from contracts.profile import (
    EditablePreferences,
    HardConstraints,
    LockedAttribute,
    StyleVectors,
    UserPreferenceProfile,
)


class TestEmptyProfile:
    def test_empty_profile_is_valid(self):
        profile = UserPreferenceProfile()
        assert profile.schema_version == 1
        assert isinstance(profile.user_id, UUID)
        assert isinstance(profile.last_updated, datetime)

    def test_cold_start_detected(self):
        profile = UserPreferenceProfile()
        assert profile.is_cold_start is True

    def test_all_layers_have_empty_defaults(self):
        profile = UserPreferenceProfile()
        assert profile.hard_constraints.sizes == []
        assert profile.hard_constraints.max_price_eur is None
        assert profile.hard_constraints.regions == []
        assert profile.hard_constraints.excluded_conditions == []
        assert profile.editable_preferences.liked_brands == []
        assert profile.editable_preferences.rejected_brands == []
        assert profile.editable_preferences.locked_attributes == []
        assert profile.vectors.positive == []
        assert profile.vectors.negative == []

    def test_serialization_roundtrip(self):
        profile = UserPreferenceProfile()
        restored = UserPreferenceProfile.model_validate_json(
            profile.model_dump_json()
        )
        assert restored == profile

    def test_json_is_valid_json(self):
        profile = UserPreferenceProfile()
        parsed = json.loads(profile.model_dump_json())
        assert parsed["schema_version"] == 1
        assert "user_id" in parsed


class TestFilledProfile:
    def _make_full_profile(self) -> UserPreferenceProfile:
        return UserPreferenceProfile(
            event_count=42,
            hard_constraints=HardConstraints(
                sizes=["M", "L"],
                max_price_eur=120.0,
                regions=["FR", "BE"],
                excluded_conditions=["fair"],
            ),
            editable_preferences=EditablePreferences(
                liked_brands=["Nike", "Adidas"],
                rejected_brands=["Fast Fashion Co"],
                locked_attributes=[
                    LockedAttribute(attribute="color", value="black", weight=2.0)
                ],
            ),
            vectors=StyleVectors(
                positive=[0.1] * 512,
                negative=[-0.05] * 512,
                embedding_version="fashionsiglip-v1",
                vector_dim=512,
            ),
        )

    def test_filled_profile_is_valid(self):
        profile = self._make_full_profile()
        assert profile.event_count == 42
        assert profile.hard_constraints.max_price_eur == 120.0
        assert "Nike" in profile.editable_preferences.liked_brands
        assert len(profile.vectors.positive) == 512

    def test_not_cold_start_when_vectors_present(self):
        profile = self._make_full_profile()
        assert profile.is_cold_start is False

    def test_serialization_roundtrip(self):
        profile = self._make_full_profile()
        restored = UserPreferenceProfile.model_validate_json(
            profile.model_dump_json()
        )
        assert restored == profile

    def test_dict_roundtrip(self):
        profile = self._make_full_profile()
        restored = UserPreferenceProfile.model_validate(profile.model_dump())
        assert restored == profile

    def test_locked_attribute_fields(self):
        profile = self._make_full_profile()
        locked = profile.editable_preferences.locked_attributes[0]
        assert locked.attribute == "color"
        assert locked.value == "black"
        assert locked.weight == 2.0

    def test_vector_dim_default(self):
        v = StyleVectors()
        assert v.vector_dim == 512
        assert v.embedding_version == "fashionsiglip-v1"

    def test_schema_version_is_1(self):
        profile = self._make_full_profile()
        assert profile.schema_version == 1
