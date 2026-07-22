from app.services.rag.knowledge_retriever import KnowledgeRetriever


class _FakeGraph:
    def __init__(self):
        self.last_query = None
        self.last_params = None

    def run_query(self, query, parameters=None):
        self.last_query = query
        self.last_params = parameters or {}
        return [{"text": "t", "category": "Security", "source": "s", "title": "T", "score": 0.9}]


class _FakeEmbeddings:
    def embed_query(self, text):
        return [0.1, 0.2, 0.3]


def _retriever():
    kr = KnowledgeRetriever()
    kr.graph = _FakeGraph()
    kr.embedding_service = _FakeEmbeddings()
    return kr


def test_search_without_categories_uses_plain_vector_query():
    kr = _retriever()
    results = kr.search("some query", k=5)

    assert len(results) == 1
    q = kr.graph.last_query
    assert "db.index.vector.queryNodes" in q
    assert "WHERE node.category" not in q          # no category filter
    assert kr.graph.last_params["k"] == 5
    assert kr.graph.last_params["vector"] == [0.1, 0.2, 0.3]


def test_search_with_categories_overfetches_and_filters():
    kr = _retriever()
    kr.overfetch = 5
    kr.search("q", k=4, categories=["Security", "Performance"])

    q = kr.graph.last_query
    assert "WHERE node.category IN $categories" in q
    p = kr.graph.last_params
    assert p["k"] == 4
    assert p["fetch"] == 20                          # k * overfetch
    assert p["categories"] == ["Security", "Performance"]


def test_default_k_falls_back_to_repository_top_k():
    kr = _retriever()
    kr.default_k = 8
    kr.search("q")
    assert kr.graph.last_params["k"] == 8
