"""AI Gateway — EmbeddingProvider (MVP-FR-034). One interface, env-selected adapter.

EMBEDDING_PROVIDER=local  → intfloat/multilingual-e5-small via sentence-transformers (CPU, 384 dims)
EMBEDDING_PROVIDER=api    → OpenAI-compatible /embeddings (LLM_BASE_URL + LLM_API_KEY + EMBEDDING_MODEL)
EMBEDDING_PROVIDER=fake   → deterministic hashing vectors (tests only)

The model loads in a background thread at startup; until it is ready (or if it fails) the matcher
uses the rules/full-text fallback, so the counter never blocks on AI.
"""
import hashlib
import logging
import math
import os
import re
import threading
import time
from typing import Optional

log = logging.getLogger("sitedesk.embedding")

PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")
MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
DIM = int(os.getenv("EMBEDDING_DIMENSION", "384"))


class EmbeddingProvider:
    name = "base"

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    # e5 convention: "query: " for the customer line, "passage: " for catalog items
    def embed_queries(self, texts: list[str]) -> list[list[float]]:
        return self.embed([f"query: {t}" for t in texts])

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        return self.embed([f"passage: {t}" for t in texts])


class LocalE5(EmbeddingProvider):
    name = "local"

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer  # heavy import, done lazily

        self.model = SentenceTransformer(MODEL, device="cpu")

    def embed(self, texts):
        return self.model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False).tolist()


class ApiEmbedding(EmbeddingProvider):
    name = "api"

    def __init__(self) -> None:
        import httpx

        base, key = os.getenv("LLM_BASE_URL", ""), os.getenv("LLM_API_KEY", "")
        if not base or not key:
            raise RuntimeError("EMBEDDING_PROVIDER=api needs LLM_BASE_URL and LLM_API_KEY")
        self.client = httpx.Client(base_url=base.rstrip("/"), headers={"Authorization": f"Bearer {key}"}, timeout=10)

    def embed(self, texts):
        r = self.client.post("/embeddings", json={"model": MODEL, "input": texts})
        r.raise_for_status()
        return [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]


class FakeEmbedding(EmbeddingProvider):
    """Bag-of-character-trigrams hashed into DIM buckets. Deterministic; only for tests."""
    name = "fake"

    def embed(self, texts):
        out = []
        for t in texts:
            t = re.sub(r"^(query|passage): ", "", t.lower())
            v = [0.0] * DIM
            for i in range(len(t) - 2):
                v[int(hashlib.md5(t[i:i + 3].encode()).hexdigest(), 16) % DIM] += 1.0
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / n for x in v])
        return out


_provider: Optional[EmbeddingProvider] = None
_state = {"status": "not_loaded", "error": None, "load_seconds": None}
_lock = threading.Lock()


def _build() -> EmbeddingProvider:
    if PROVIDER == "fake":
        return FakeEmbedding()
    if PROVIDER == "api":
        return ApiEmbedding()
    return LocalE5()


def load() -> Optional[EmbeddingProvider]:
    global _provider
    with _lock:
        if _provider is not None or _state["status"] == "error":
            return _provider
        _state["status"] = "loading"
        t = time.perf_counter()
        try:
            p = _build()
            p.embed_queries(["warm-up"])  # first call is slow; pay it at startup, not in the demo
            _provider = p
            _state.update(status="up", load_seconds=round(time.perf_counter() - t, 1))
            log.warning("embedding provider %s/%s ready in %.1fs", PROVIDER, MODEL, time.perf_counter() - t)
        except Exception as e:  # noqa: BLE001
            _state.update(status="error", error=str(e)[:200])
            log.warning("embedding provider failed: %s — matcher stays on rules fallback", e)
        return _provider


def load_in_background(after=None) -> None:
    def run():
        if load() and after:
            try:
                after()
            except Exception as e:  # noqa: BLE001
                log.warning("post-load hook failed: %s", e)

    threading.Thread(target=run, daemon=True, name="embedding-loader").start()


def get() -> Optional[EmbeddingProvider]:
    """Ready provider or None (never blocks a request on model loading)."""
    return _provider


def status() -> dict:
    return {"provider": PROVIDER, "model": MODEL, **_state}


def set_provider_for_tests(p: Optional[EmbeddingProvider]) -> None:
    global _provider
    _provider = p
    _state["status"] = "up" if p else "not_loaded"


def product_passage(p: dict) -> str:
    """Text that represents a catalog item in the vector index."""
    specs = p.get("technical_specs") or {}
    spec_txt = " ".join(f"{k.replace('_', ' ')} {', '.join(v) if isinstance(v, list) else v}" for k, v in specs.items())
    aliases = " | ".join(a for v in (p.get("aliases") or {}).values() for a in v)
    return f"{p['name']}. {p['category']}. {spec_txt}. {aliases}"
