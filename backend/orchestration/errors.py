from __future__ import annotations


class OrchestratorError(Exception):
    """Base class for all orchestration-layer errors."""


class EmbeddingError(OrchestratorError):
    """Raised when the embedding module fails."""


class RetrievalError(OrchestratorError):
    """Raised when the retrieval module fails."""


class RankingError(OrchestratorError):
    """Raised when the ranking module fails."""


class PolicyError(OrchestratorError):
    """Raised when the policy/diversity module fails."""


class ExplainerError(OrchestratorError):
    """Raised when the explainability module fails."""
