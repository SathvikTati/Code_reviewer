from app.services.rag.hierarchical_retriever import HierarchicalRetriever


class _FakeRetriever:
    def retrieve_repository_tree(self):
        return [
            {"file": {"relative_path": "app/auth/login.py"},
             "classes": ["LoginService", None], "functions": ["verify", None]},
            {"file": {"relative_path": "app/utils/text.py"},
             "classes": [], "functions": ["slugify"]},
        ]


class _FakeKnowledge:
    def __init__(self):
        self.calls = []

    def search(self, query_text, k=None, categories=None):
        self.calls.append({"query": query_text, "k": k, "categories": categories})
        return [{"category": (categories or ["X"])[0], "title": "Std",
                 "text": "t", "source": "s", "score": 0.8}]


def _hr():
    hr = HierarchicalRetriever()
    hr.retriever = _FakeRetriever()
    hr.knowledge_retriever = _FakeKnowledge()
    hr.module_k = 4
    return hr


def test_retrieve_groups_and_attaches_standards():
    hr = _hr()
    result = hr.retrieve()

    names = [m["name"] for m in result["modules"]]
    assert "authentication" in names
    assert "utilities" in names

    auth = next(m for m in result["modules"] if m["name"] == "authentication")
    # falsy class/function entries are filtered out
    assert auth["files"][0]["classes"] == ["LoginService"]
    assert auth["files"][0]["functions"] == ["verify"]
    assert auth["standards"] and auth["standards"][0]["title"] == "Std"


def test_module_query_and_category_bias_passed_to_search():
    hr = _hr()
    hr.retrieve()

    calls = hr.knowledge_retriever.calls
    auth_call = next(c for c in calls if c["query"].startswith("authentication module"))
    assert auth_call["k"] == 4
    assert auth_call["categories"] == ["Security"]
    assert "app/auth/login.py" in auth_call["query"]
