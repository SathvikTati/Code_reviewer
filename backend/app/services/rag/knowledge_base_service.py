from pathlib import Path

from app.config.settings import settings
from app.services.graph.graph_service import GraphService
from app.services.rag.chunker import MarkdownChunker
from app.services.rag.embedding_service import EmbeddingService


VECTOR_INDEX_NAME = "knowledge_chunk_embedding"
CHUNK_LABEL = "KnowledgeChunk"


class KnowledgeBaseService:
    """Ingests the software-engineering best-practices knowledge base into
    Neo4j as KnowledgeChunk nodes with embedding vectors, backed by a native
    vector index for semantic retrieval."""

    def __init__(self, knowledge_base_dir: str | None = None):

        self.graph = GraphService()
        self.chunker = MarkdownChunker()
        self.embedding_service = EmbeddingService()

        if knowledge_base_dir:
            self.base_dir = Path(knowledge_base_dir)
        else:
            self.base_dir = settings.knowledge_base_dir

    def ingest(self) -> int:
        """(Re)builds the knowledge base. Returns the number of chunks stored."""

        chunks = self._load_chunks()

        if not chunks:
            raise RuntimeError(
                f"No knowledge base documents found under {self.base_dir}"
            )

        # Embed everything FIRST (before touching the DB) so a failure here
        # doesn't leave the index dropped / nodes cleared.
        print(
            f"Embedding {len(chunks)} chunks with {self.embedding_service.model} ..."
        )

        def _progress(done, total):
            print(f"  embedded {done}/{total}", end="\r", flush=True)

        vectors = self.embedding_service.embed_documents(
            [chunk.text for chunk in chunks], progress=_progress
        )
        print()  # newline after the progress line

        dimensions = len(vectors[0])

        self._create_constraint()
        # Drop the old index first: its dimensionality is fixed at creation, so
        # switching embedding provider (e.g. 768 -> 1536) requires rebuilding it.
        self.graph.drop_vector_index(VECTOR_INDEX_NAME)
        self._clear_existing()

        print(f"Writing {len(chunks)} chunks to Neo4j ...")
        for chunk, embedding in zip(chunks, vectors):
            self.graph.create_node(
                CHUNK_LABEL,
                {
                    "id": chunk.id,
                    "text": chunk.text,
                    "category": chunk.category,
                    "source": chunk.source,
                    "title": chunk.title,
                },
            )
            self.graph.set_node_vector(CHUNK_LABEL, chunk.id, "embedding", embedding)

        self.graph.create_vector_index(
            VECTOR_INDEX_NAME, CHUNK_LABEL, "embedding", dimensions
        )

        return len(chunks)

    def _load_chunks(self) -> list:

        chunks = []

        for path in sorted(self.base_dir.rglob("*.md")):
            chunks.extend(self.chunker.chunk_file(path, self.base_dir))

        return chunks

    def _create_constraint(self):

        query = f"""
        CREATE CONSTRAINT knowledge_chunk_id
        IF NOT EXISTS
        FOR (n:{CHUNK_LABEL})
        REQUIRE n.id IS UNIQUE
        """

        self.graph.run_query(query)

    def _clear_existing(self):

        query = f"""
        MATCH (n:{CHUNK_LABEL})
        DETACH DELETE n
        """

        self.graph.run_query(query)
