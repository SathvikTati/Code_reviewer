from fastapi.testclient import TestClient

import app.main as main
from app.api import review_controller


client = TestClient(main.app)


def test_index_serves_frontend():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Code Review Assistant" in r.text


def test_analyze_returns_analysis_and_usage(monkeypatch):
    def fake_analyze(url):
        assert url == "https://github.com/o/repo"
        return {"report": "# Audit\nAll good.",
                "usage": {"total_tokens": 42, "llm_calls": 1}}

    monkeypatch.setattr(review_controller.review_service, "analyze_repository", fake_analyze)

    r = client.post("/review/analyze", json={"github_url": "https://github.com/o/repo"})
    assert r.status_code == 200
    body = r.json()
    assert body["analysis"] == "# Audit\nAll good."
    assert body["usage"]["total_tokens"] == 42


def test_analyze_requires_github_url():
    r = client.post("/review/analyze", json={})
    assert r.status_code == 422   # pydantic validation error
