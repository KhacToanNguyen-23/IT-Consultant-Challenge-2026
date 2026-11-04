"""Embedding provider boundary for catalog indexing and query matching."""

import os
from abc import ABC, abstractmethod

from openai import OpenAI


EMBEDDING_DIMENSIONS = 384
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


class EmbeddingProvider(ABC):
    """Provider-neutral interface so local embedding models can be added later."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one fixed-width embedding for every input text."""


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str = DEFAULT_EMBEDDING_MODEL) -> None:
        self.model = model
        self.client = OpenAI(api_key=api_key, timeout=15.0, max_retries=1)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=EMBEDDING_DIMENSIONS,
            encoding_format="float",
        )
        return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]


def get_embedding_provider() -> EmbeddingProvider | None:
    """Return the configured provider, or None when semantic matching is disabled."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    provider_name = os.getenv("EMBEDDING_PROVIDER", "openai").strip().lower()
    if provider_name != "openai":
        raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider_name}")
    return OpenAIEmbeddingProvider(api_key=api_key)
