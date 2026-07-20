from __future__ import annotations
from contracts.interfaces import CandidateSet, HardConstraints, StyleVector

async def retrieve_candidates(
    style_vector: StyleVector,
    hard_constraints: HardConstraints,
    top_k: int = 200,
) -> CandidateSet:
    # pgvector HNSW cosine. Latency < 100 ms CPU.
    # Fallback: recent products matching hard constraints.
    raise NotImplementedError
