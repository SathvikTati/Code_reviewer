from app.services.rag.embedding_service import (
    EmbeddingService,
    _OllamaEmbedder,
    _OpenAIEmbedder,
)


def test_ollama_embedder_uses_task_prefixes():
    e = _OllamaEmbedder.__new__(_OllamaEmbedder)  # avoid constructing the client
    assert e.query_text("x") == "search_query: x"
    assert e.document_text("x") == "search_document: x"


def test_openai_embedder_has_no_prefixes():
    e = _OpenAIEmbedder.__new__(_OpenAIEmbedder)
    assert e.query_text("x") == "x"
    assert e.document_text("x") == "x"


def test_provider_selection(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
    assert isinstance(EmbeddingService().backend, _OllamaEmbedder)

    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert isinstance(EmbeddingService().backend, _OpenAIEmbedder)


class _FakeBackend:
    span_name = "fake.embeddings"
    model = "fake-model"

    def __init__(self):
        self.received = None

    def query_text(self, t):
        return t

    def document_text(self, t):
        return t

    def embed(self, text):
        self.received = text
        return [0.0, 0.1, 0.2]


def test_truncates_input_to_max_input_chars(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
    svc = EmbeddingService()
    svc.max_input_chars = 100
    fake = _FakeBackend()
    svc.backend = fake

    vec = svc.embed_query("x" * 5000)
    assert vec == [0.0, 0.1, 0.2]
    assert len(fake.received) == 100        # truncated before embedding


def test_short_input_not_truncated(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
    svc = EmbeddingService()
    svc.max_input_chars = 100
    fake = _FakeBackend()
    svc.backend = fake

    svc.embed_document("hello")
    assert fake.received == "hello"
