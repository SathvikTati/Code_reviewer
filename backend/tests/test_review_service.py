from app.services.review.review_service import ReviewService


def test_collect_module_code_reads_real_source(tmp_path):
    (tmp_path / "a.py").write_text("def a():\n    return 1\n")
    (tmp_path / "b.py").write_text("def b():\n    return 2\n")

    rs = ReviewService()
    module = {"files": [
        {"relative_path": "a.py"},
        {"relative_path": "b.py"},
    ]}
    path_map = {"a.py": str(tmp_path / "a.py"), "b.py": str(tmp_path / "b.py")}

    code, included, truncated, skipped = rs._collect_module_code(module, path_map)

    assert included == 2 and skipped == 0 and truncated == 0
    assert "--- a.py ---" in code and "def a()" in code
    assert "--- b.py ---" in code and "def b()" in code


def test_collect_module_code_truncates_large_files(tmp_path, monkeypatch):
    monkeypatch.setenv("RESOURCES_DIR", "")  # keep real config
    big = "x = 1\n" * 2000
    (tmp_path / "big.py").write_text(big)

    rs = ReviewService()
    module = {"files": [{"relative_path": "big.py"}]}
    path_map = {"big.py": str(tmp_path / "big.py")}

    code, included, truncated, skipped = rs._collect_module_code(module, path_map)
    assert included == 1
    assert truncated == 1
    assert "truncated" in code                      # per-file cap applied
    # code block should be far smaller than the original file
    assert len(code) < len(big)


def test_collect_module_code_handles_missing_paths(tmp_path):
    rs = ReviewService()
    module = {"files": [{"relative_path": "ghost.py"}]}
    code, included, truncated, skipped = rs._collect_module_code(module, {})
    assert code == "" and included == 0


def test_format_coverage_is_honest():
    rs = ReviewService()
    note = rs._format_coverage(total=100, reviewed=40, truncated=5, skipped=10, modules=6)
    assert "40 of 100" in note and "40%" in note
    assert "6 module" in note
    assert "truncated" in note and "skipped" in note
    assert "reviewed code only" in note


def test_format_summaries_empty_and_populated():
    rs = ReviewService()
    assert "no analyzable Python files" in rs._format_summaries([])
    out = rs._format_summaries([{"module": "api", "summary": "ok"}])
    assert "### Module: api" in out and "ok" in out


def test_map_reduce_flow_reviews_each_module_then_aggregates(tmp_path):
    """clone/scan/parse/graph/retrieve/LLM are all mocked; verifies the
    two-phase orchestration: one review per module, then one final call."""
    from app.models.repository import Repository
    from app.models.python_file import PythonFile

    (tmp_path / "login.py").write_text("def verify():\n    return True\n")
    (tmp_path / "util.py").write_text("def slug(s):\n    return s.lower()\n")

    repo = Repository(
        name="demo", github_url="https://github.com/o/demo", local_path=str(tmp_path),
        files=[
            PythonFile(id="login.py", name="login.py", relative_path="login.py",
                       absolute_path=str(tmp_path / "login.py"), size=10),
            PythonFile(id="util.py", name="util.py", relative_path="util.py",
                       absolute_path=str(tmp_path / "util.py"), size=10),
        ],
    )

    hierarchy = {"modules": [
        {"name": "authentication", "categories": ["Security"],
         "files": [{"relative_path": "login.py", "classes": [], "functions": ["verify"]}],
         "standards": []},
        {"name": "utilities", "categories": ["Code Quality"],
         "files": [{"relative_path": "util.py", "classes": [], "functions": ["slug"]}],
         "standards": []},
    ]}

    class FakeLLM:
        def __init__(self):
            self.prompts = []
        def generate(self, prompt):
            self.prompts.append(prompt)
            return f"OUT#{len(self.prompts)}"

    rs = ReviewService()
    fake_llm = FakeLLM()
    rs.clone_service.clone_repository = lambda url: repo
    rs.clone_service.delete_repository = lambda p: None
    rs.scanner_service.scan = lambda r: r
    rs.parser_service.parse = lambda r: r
    rs.graph_builder.build = lambda r: None
    rs.hierarchical_retriever.retrieve = lambda: hierarchy
    rs.llm_service = fake_llm

    result = rs.analyze_repository("https://github.com/o/demo")

    # 2 module reviews + 1 final report = 3 LLM calls
    assert len(fake_llm.prompts) == 3
    assert result["modules"] == ["authentication", "utilities"]
    assert result["report"] == "OUT#3"                 # final (reduce) output

    # phase-1 prompts contained the REAL code
    assert any("def verify()" in p for p in fake_llm.prompts[:2])
    assert any("def slug(s)" in p for p in fake_llm.prompts[:2])
    # phase-2 prompt consolidated the module summaries
    assert "### Module: authentication" in fake_llm.prompts[2]
    assert "OUT#1" in fake_llm.prompts[2]
