"""Grounded, deterministic explanations for ranked products.

The module deliberately only reads ``RankedItem.score_breakdown`` values emitted
by the transparent ranker.  It never infers a preference from product text.
"""
from __future__ import annotations

from dataclasses import dataclass

from contracts.pipeline import Explanation, RankedFeed, RankedItem
from contracts.product import ProductRecord
from contracts.profile import UserPreferenceProfile


@dataclass(frozen=True)
class _Reason:
    score: float
    phrase: str
    evidence_ref: str


def _product_tags(product: ProductRecord) -> list[str]:
    """Return safe, user-editable fallback tags from stored product fields."""
    return [
        value
        for value in (product.brand, product.category, product.condition.value)
        if value
    ]


def _reasons(
    product: ProductRecord,
    scores: dict[str, float],
    profile: UserPreferenceProfile,
) -> list[_Reason]:
    """Build candidate reasons exclusively from real ranker features."""
    reasons: list[_Reason] = []
    liked_brands = {
        brand.casefold() for brand in profile.editable_preferences.liked_brands
    }
    brand_score = scores.get("brand_boost", 0.0)
    if product.brand and product.brand.casefold() in liked_brands and brand_score > 0:
        reasons.append(_Reason(
            score=brand_score,
            phrase=f"Tu aimes {product.brand}",
            evidence_ref=f"feature:brand_boost={brand_score:.3f}",
        ))

    similarity = scores.get("similarity", 0.0)
    if similarity > 0:
        reasons.append(_Reason(
            score=similarity,
            phrase="Proche de tes inspirations",
            evidence_ref=f"feature:similarity={similarity:.3f}",
        ))

    price_fit = scores.get("price_fit", 0.0)
    if price_fit > 0:
        reasons.append(_Reason(
            score=price_fit,
            phrase="Dans ton budget",
            evidence_ref=f"feature:price_fit={price_fit:.3f}",
        ))

    freshness = scores.get("freshness", 0.0)
    if freshness > 0:
        reasons.append(_Reason(
            score=freshness,
            phrase="Nouvellement ajouté",
            evidence_ref=f"feature:freshness={freshness:.3f}",
        ))
    return sorted(reasons, key=lambda reason: reason.score, reverse=True)


def explain(
    product: ProductRecord,
    ranked_scores: dict[str, float],
    profile: UserPreferenceProfile,
) -> Explanation:
    """Explain a product from its persisted ranking evidence.

    At most two strongest reasons are exposed.  If no ranking feature carries
    evidence, the caller receives only editable product tags rather than a
    fabricated sentence.
    """
    selected = _reasons(product, ranked_scores, profile)[:2]
    if not selected:
        return Explanation(product_id=product.id, editable_tags=_product_tags(product))

    phrases = [reason.phrase for reason in selected]
    return Explanation(
        product_id=product.id,
        reasons=phrases,
        evidence_refs=[reason.evidence_ref for reason in selected],
        grounded=True,
        editable_tags=_product_tags(product),
        sentence=" · ".join(phrases),
    )


class GroundedExplainer:
    """Adapter used by the orchestrator's ``ExplainerProtocol``."""

    def explain(
        self, feed: RankedFeed, profile: UserPreferenceProfile,
    ) -> list[Explanation]:
        explanations: list[Explanation] = []
        for item in feed.items:
            explanations.append(
                explain(item.product, item.score_breakdown, profile)
            )
        return explanations


def fallback_explanation(item: RankedItem) -> Explanation:
    """Expose the documented no-generated-sentence fallback for adapters."""
    return Explanation(
        product_id=item.product.id,
        editable_tags=_product_tags(item.product),
    )
