from types import SimpleNamespace

from app.services.builders.context_builder import ContextBuilder


def _hierarchy():
    std_a = {"category": "Security", "title": "Password Handling",
             "text": "Use argon2.", "source": "security/x.md", "score": 0.70}
    std_a_better = {**std_a, "score": 0.90}  # same (source,title), higher score
    std_b = {"category": "Code Quality", "title": "Small Functions",
             "text": "Do one thing.", "source": "cq/clean.md", "score": 0.80}
    return {
        "modules": [
            {"name": "authentication", "categories": ["Security"],
             "files": [{"relative_path": "auth/login.py",
                        "classes": ["LoginService"], "functions": ["verify"]}],
             "standards": [std_a]},
            {"name": "services", "categories": ["Code Quality"],
             "files": [{"relative_path": "svc/x.py", "classes": [], "functions": ["run"]}],
             "standards": [std_a_better, std_b]},
        ]
    }


def test_merge_standards_dedupes_and_sorts_by_score():
    cb = ContextBuilder()
    merged = cb.merge_standards(_hierarchy())

    # std_a and std_a_better share (source,title) -> one entry, highest score kept
    titles = [s["title"] for s in merged]
    assert titles.count("Password Handling") == 1
    # sorted by score desc: Password Handling (0.90) before Small Functions (0.80)
    assert merged[0]["title"] == "Password Handling"
    assert merged[0]["score"] == 0.90
    assert merged[1]["title"] == "Small Functions"


def test_build_hierarchical_context_lists_modules_files_and_standards():
    cb = ContextBuilder()
    repo = SimpleNamespace(name="demo", github_url="https://github.com/o/demo")
    text = cb.build_hierarchical_context(repo, _hierarchy())

    assert "Name: demo" in text
    assert "=== Module: authentication ===" in text
    assert "Focus areas: Security" in text
    assert "auth/login.py" in text
    assert "classes: LoginService" in text
    assert "functions: verify" in text
    assert "Applicable standards:" in text
    assert "[Security] Password Handling" in text


def test_build_repository_context_handles_empty():
    cb = ContextBuilder()
    assert cb.build_repository_context([]) == "Repository not found."
