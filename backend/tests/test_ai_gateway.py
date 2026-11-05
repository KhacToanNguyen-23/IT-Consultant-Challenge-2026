"""MVP-FR-034 / NFR-007: one AI Gateway interface, adapters chosen by env, provider swaps do not change the API,
and no secret ever appears in a response. Unit tests need no database; the last two are integration tests (conftest)."""
import pytest

from ai import embedding, llm


@pytest.fixture
def clean_gateway():
    saved = (llm._provider, llm._configured, embedding._provider, dict(embedding._state), embedding.PROVIDER)
    yield
    llm._provider, llm._configured, embedding._provider = saved[0], saved[1], saved[2]
    embedding._state.clear()
    embedding._state.update(saved[3])
    embedding.PROVIDER = saved[4]


def test_llm_is_disabled_unless_all_env_values_are_present(clean_gateway, monkeypatch):
    for key in ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    llm._provider, llm._configured = None, False
    assert llm.get() is None and llm.status() == "disabled"
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example")
    monkeypatch.setenv("LLM_MODEL", "some-model")  # still no key
    llm._provider, llm._configured = None, False
    assert llm.status() == "disabled"


def test_llm_adapter_is_selected_by_env_only_and_the_status_never_leaks_the_key(clean_gateway, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example")
    monkeypatch.setenv("LLM_MODEL", "some-model")
    monkeypatch.setenv("LLM_API_KEY", "sk-super-secret-value")
    llm._provider, llm._configured = None, False
    assert llm.status() == "openai_compatible"
    assert "sk-super-secret-value" not in llm.status()


def test_unknown_llm_provider_name_means_disabled_not_a_crash(clean_gateway, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "something-else")
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example")
    monkeypatch.setenv("LLM_MODEL", "m")
    monkeypatch.setenv("LLM_API_KEY", "k")
    llm._provider, llm._configured = None, False
    assert llm.get() is None


def test_embedding_api_adapter_without_credentials_fails_soft(clean_gateway, monkeypatch):
    monkeypatch.setattr(embedding, "PROVIDER", "api")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    embedding._provider = None
    embedding._state.update(status="not_loaded", error=None, load_seconds=None)
    assert embedding.load() is None  # the matcher then stays on the rules fallback
    st = embedding.status()
    assert st["status"] == "error" and st["error"] and "key" not in st["error"].lower().replace("api_key", "")


def test_embedding_dimension_matches_the_database_column():
    from db.models import Product

    vec = embedding.FakeEmbedding().embed_queries(["timber 45x95 C24"])[0]
    assert len(vec) == embedding.DIM == Product.embedding.type.dim == 384


def test_fake_and_real_adapters_share_one_interface():
    for adapter in (embedding.FakeEmbedding, embedding.LocalE5, embedding.ApiEmbedding):
        assert issubclass(adapter, embedding.EmbeddingProvider)
    for method in ("embed", "embed_queries", "embed_passages"):
        assert callable(getattr(embedding.EmbeddingProvider, method))
    assert issubclass(llm.FakeLLM, llm.LLMProvider) and issubclass(llm.OpenAICompatible, llm.LLMProvider)


# ------------------------------------------------------------------ integration (needs Postgres, see conftest)
def test_swapping_the_embedding_provider_does_not_change_the_api_shape(counter):
    class Shifted(embedding.FakeEmbedding):  # a different "model": same interface, different vectors
        def embed(self, texts):
            return [list(reversed(v)) for v in super().embed(texts)]

    shapes = []
    for provider in (embedding.FakeEmbedding(), Shifted()):
        embedding.set_provider_for_tests(provider)
        sid = counter.open("120 m timber 45x95 C24\n5 poser cement 25 kg")
        v = counter.analyze(sid)
        shapes.append((sorted(v), [sorted(l) for l in v["lines"]], [sorted(l["match"]) for l in v["lines"]]))
    assert shapes[0] == shapes[1]


def test_health_response_never_contains_a_secret(counter, monkeypatch, clean_gateway):
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example")
    monkeypatch.setenv("LLM_MODEL", "m")
    monkeypatch.setenv("LLM_API_KEY", "sk-super-secret-value")
    llm._provider, llm._configured = None, False
    r = counter.call("GET", "/health")
    assert r.status_code == 200 and "sk-super-secret-value" not in r.text and r.json()["llm"] == "openai_compatible"
