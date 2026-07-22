import os

from dotenv import load_dotenv
from ollama import Client

from app.config.settings import settings
from app.telemetry import tracing
from app.telemetry import usage

load_dotenv()


class _OllamaEmbedder:
    """nomic-embed-text via Ollama. Uses task-specific prefixes
    ('search_document: ' / 'search_query: ') which improve retrieval quality."""

    span_name = "ollama.embeddings"
    supports_batch = False

    def __init__(self):
        self.client = Client(host=os.getenv("OLLAMA_HOST"))
        self.model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    def query_text(self, text: str) -> str:
        return f"search_query: {text}"

    def document_text(self, text: str) -> str:
        return f"search_document: {text}"

    def embed(self, text: str) -> list[float]:
        return self.client.embeddings(model=self.model, prompt=text)["embedding"]


class _OpenAIEmbedder:
    """OpenAI embeddings (e.g. text-embedding-3-small). No task prefixes.
    Supports batching many inputs in a single API call."""

    span_name = "openai.embeddings"
    supports_batch = True

    def __init__(self):
        from openai import OpenAI

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL") or None,
        )
        self.model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

    def query_text(self, text: str) -> str:
        return text

    def document_text(self, text: str) -> str:
        return text

    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        # One API call for many inputs (order preserved).
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


class EmbeddingService:
    """Generates embeddings through the provider selected by EMBEDDING_PROVIDER
    ('ollama' by default, or 'openai'). Shared truncation, tracing, and usage
    accounting live here; the backend only supplies text preparation and the
    raw embedding call.

    NOTE: switching provider changes the vector dimension (nomic=768,
    text-embedding-3-small=1536), so you must re-ingest the knowledge base
    after changing it (the Neo4j vector index is sized at ingest time).
    """

    def __init__(self):

        provider = os.getenv("EMBEDDING_PROVIDER", "ollama").strip().lower()

        if provider == "openai":
            self.backend = _OpenAIEmbedder()
        else:
            self.backend = _OllamaEmbedder()

        self.model = self.backend.model

        # Guard against the model's context window; large inputs are truncated.
        self.max_input_chars = settings.get(
            "embedding", "max_input_chars", default=4000
        )

    def _truncate(self, text: str) -> str:
        return text[: self.max_input_chars] if len(text) > self.max_input_chars else text

    def _embed(self, text: str) -> list[float]:

        text = self._truncate(text)

        with tracing.span(
            self.backend.span_name,
            kind=tracing.KIND_EMBEDDING,
            attributes={
                tracing.EMBEDDING_MODEL_NAME: self.model,
                "embedding.input_chars": len(text),
            },
        ) as current:

            embedding = self.backend.embed(text)

            usage.record_embedding()

            if current is not None:
                current.set_attribute("embedding.dimensions", len(embedding))

            return embedding

    def embed_document(self, text: str) -> list[float]:
        return self._embed(self.backend.document_text(text))

    def embed_query(self, text: str) -> list[float]:
        return self._embed(self.backend.query_text(text))

    def embed_documents(
        self, texts: list[str], progress=None
    ) -> list[list[float]]:
        """Embeds many documents. Batches into a single API call per chunk of
        `batch_size` when the backend supports it (OpenAI); otherwise falls back
        to one call per document (Ollama). `progress(done, total)` is invoked
        after each batch/item so callers can show progress."""

        prepared = [self._truncate(self.backend.document_text(t)) for t in texts]
        total = len(prepared)

        if not getattr(self.backend, "supports_batch", False):
            vectors = []
            for i, text in enumerate(prepared, 1):
                vectors.append(self._embed_prepared(text))
                if progress:
                    progress(i, total)
            return vectors

        batch_size = settings.get("embedding", "batch_size", default=96)
        vectors: list[list[float]] = []

        for start in range(0, total, batch_size):
            batch = prepared[start:start + batch_size]
            with tracing.span(
                self.backend.span_name,
                kind=tracing.KIND_EMBEDDING,
                attributes={
                    tracing.EMBEDDING_MODEL_NAME: self.model,
                    "embedding.batch_size": len(batch),
                },
            ) as current:
                batch_vectors = self.backend.embed_batch(batch)
                for _ in batch:
                    usage.record_embedding()
                if current is not None and batch_vectors:
                    current.set_attribute("embedding.dimensions", len(batch_vectors[0]))
            vectors.extend(batch_vectors)
            if progress:
                progress(min(start + batch_size, total), total)

        return vectors

    def _embed_prepared(self, text: str) -> list[float]:
        """Embeds already-prepared (prefixed + truncated) text."""
        with tracing.span(
            self.backend.span_name,
            kind=tracing.KIND_EMBEDDING,
            attributes={
                tracing.EMBEDDING_MODEL_NAME: self.model,
                "embedding.input_chars": len(text),
            },
        ) as current:
            embedding = self.backend.embed(text)
            usage.record_embedding()
            if current is not None:
                current.set_attribute("embedding.dimensions", len(embedding))
            return embedding
