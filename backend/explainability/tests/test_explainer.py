from __future__ import annotations

from contracts.pipeline import RankedFeed, RankedItem
from contracts.product import ProductCondition, ProductRecord, ProductSource
from contracts.profile import EditablePreferences, UserPreferenceProfile
from explainability.explainer import GroundedExplainer, explain


def _product() -> ProductRecord:
    return ProductRecord(
        id="prod-1", source=ProductSource.ebay, source_record_id="1",
        title="Carhartt jacket", brand="Carhartt", price=50,
        condition=ProductCondition.good, category="jackets", image_urls=["https://img"],
    )


def _profile() -> UserPreferenceProfile:
    return UserPreferenceProfile(
        editable_preferences=EditablePreferences(liked_brands=["Carhartt"]),
    )


def test_explanation_is_grounded_in_ranker_features() -> None:
    result = explain(
        _product(),
        {"brand_boost": 1.0, "similarity": 0.9, "price_fit": 0.8}, _profile(),
    )

    assert result.grounded is True
    assert result.reasons == ["Tu aimes Carhartt", "Proche de tes inspirations"]
    assert result.evidence_refs == [
        "feature:brand_boost=1.000", "feature:similarity=0.900",
    ]
    assert len(result.reasons) == 2


def test_explainer_has_safe_tag_fallback_when_no_evidence_exists() -> None:
    result = explain(_product(), {}, _profile())

    assert result.grounded is False
    assert result.sentence is None
    assert result.editable_tags == ["Carhartt", "jackets", "good"]


def test_adapter_produces_grounded_explanations_for_ranked_feed() -> None:
    feed = RankedFeed(
        request_id="00000000-0000-0000-0000-000000000001",
        items=[RankedItem(
            product=_product(), final_score=0.9, rank=1,
            score_breakdown={"similarity": 0.9},
        )],
    )

    result = GroundedExplainer().explain(feed, _profile())

    assert result[0].grounded is True
    assert result[0].evidence_refs == ["feature:similarity=0.900"]
