"""One-time (idempotent) ingestion of the best-practices knowledge base.

Run from the backend/ directory after Neo4j is up and the nomic-embed-text
model is pulled in Ollama:

    python -m scripts.ingest_knowledge_base
"""

from app.services.rag.knowledge_base_service import KnowledgeBaseService


def main():

    service = KnowledgeBaseService()

    print(f"Ingesting knowledge base from {service.base_dir} ...")

    count = service.ingest()

    print(f"Done. Stored {count} knowledge chunks and built the vector index.")


if __name__ == "__main__":
    main()
