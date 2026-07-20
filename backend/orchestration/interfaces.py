from __future__ import annotations

from typing import Protocol

from contracts.pipeline import (
    CandidateSet,
    Explanation,
    RankedFeed,
    RecoRequest,
)
from contracts.profile import UserPreferenceProfile


class RetrieverProtocol(Protocol):
    def retrieve(self, request: RecoRequest) -> CandidateSet: ...


class RankerProtocol(Protocol):
    def rank(
        self, candidates: CandidateSet, profile: UserPreferenceProfile
    ) -> RankedFeed: ...


class PolicyProtocol(Protocol):
    def apply(
        self, feed: RankedFeed, profile: UserPreferenceProfile
    ) -> RankedFeed: ...


class ExplainerProtocol(Protocol):
    def explain(
        self, feed: RankedFeed, profile: UserPreferenceProfile
    ) -> list[Explanation]: ...
