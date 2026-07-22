from app.config.settings import settings
from app.services.graph.graph_service import GraphService
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.knowledge_base_service import VECTOR_INDEX_NAME


class KnowledgeRetriever:
    """Semantic retrieval over the best-practices knowledge base using the
    Neo4j vector index. Kept separate from the code-graph Retriever so the
    two compose: graph gives structure, this gives applicable standards."""

    def __init__(self):
        self.graph = GraphService()
        self.embedding_service = EmbeddingService()
        self.default_k = settings.get("retrieval", "repository_top_k", default=8)
        self.overfetch = settings.get("retrieval", "category_overfetch", default=5)

    def search(
        self,
        query_text: str,
        k: int | None = None,
        categories: list[str] | None = None
    ) -> list[dict]:
        """Returns the k most relevant knowledge chunks for query_text.

        When categories is given, results are restricted to those review
        categories. Because the vector search runs before filtering, we
        over-fetch and then filter/limit to keep k results per call.
        """

        if k is None:
            k = self.default_k

        query_vector = self.embedding_service.embed_query(query_text)

        if categories:

            query = """
            CALL db.index.vector.queryNodes($index, $fetch, $vector)
            YIELD node, score
            WHERE node.category IN $categories
            RETURN
                node.text AS text,
                node.category AS category,
                node.source AS source,
                node.title AS title,
                score
            LIMIT $k
            """

            parameters = {
                "index": VECTOR_INDEX_NAME,
                "fetch": max(k * self.overfetch, k),
                "vector": query_vector,
                "categories": categories,
                "k": k
            }

        else:

            query = """
            CALL db.index.vector.queryNodes($index, $k, $vector)
            YIELD node, score
            RETURN
                node.text AS text,
                node.category AS category,
                node.source AS source,
                node.title AS title,
                score
            """

            parameters = {
                "index": VECTOR_INDEX_NAME,
                "k": k,
                "vector": query_vector
            }

        return self.graph.run_query(query, parameters)
