"""Embedding providers for memory retrieval.

MVP uses deterministic embeddings (no external API keys).
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Embedding provider contract."""

    def embed(self, text: str) -> list[float]:
        """Create an embedding vector for text."""


class DeterministicEmbeddingProvider:
    """Deterministic fake embedding provider.

    Produces a stable vector of configurable dimension using SHA-256 based expansion.
    Default dimension matches current DB schema VECTOR(1536).
    """

    def __init__(self, *, dimension: int = 1536) -> None:
        self.dimension = dimension

    def embed(self, text: str) -> list[float]:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []

        counter = 0
        while len(values) < self.dimension:
            payload = seed + counter.to_bytes(4, "big", signed=False)
            digest = hashlib.sha256(payload).digest()
            counter += 1

            # 32 bytes -> 8 float-like values
            for i in range(0, len(digest), 4):
                if len(values) >= self.dimension:
                    break
                chunk = digest[i : i + 4]
                integer = int.from_bytes(chunk, "big", signed=False)
                # map uint32 to [-1, 1]
                values.append((integer / 0xFFFFFFFF) * 2.0 - 1.0)

        return _l2_normalize(values)


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Cosine similarity with safety for zero vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2, strict=False))
    n1 = math.sqrt(sum(a * a for a in v1))
    n2 = math.sqrt(sum(b * b for b in v2))
    if n1 == 0.0 or n2 == 0.0:
        return 0.0
    return dot / (n1 * n2)


def _l2_normalize(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in values))
    if norm == 0.0:
        return values
    return [v / norm for v in values]
