from app.services.builders import prompt_builder
from app.services.builders.prompt_builder import PromptBuilder, strict_knowledge_base_enabled


STANDARDS = [{
    "category": "Security", "title": "OWASP — A03: Injection",
    "text": "Never build SQL from input.", "source": "security/owasp.md", "score": 0.9,
}]


def test_format_standards_empty_and_populated():
    pb = PromptBuilder()
    assert pb.format_standards([]) == "No specific coding standards were retrieved."
    out = pb.format_standards(STANDARDS)
    assert "[Security] OWASP — A03: Injection" in out
    assert "Never build SQL from input." in out


def test_strict_flag_reads_env(monkeypatch):
    monkeypatch.setenv("STRICT_KNOWLEDGE_BASE", "true")
    assert strict_knowledge_base_enabled() is True
    monkeypatch.setenv("STRICT_KNOWLEDGE_BASE", "false")
    assert strict_knowledge_base_enabled() is False
    monkeypatch.setenv("STRICT_KNOWLEDGE_BASE", "0")
    assert strict_knowledge_base_enabled() is False


def test_strict_mode_injects_strict_directive(monkeypatch):
    monkeypatch.setenv("STRICT_KNOWLEDGE_BASE", "true")
    prompt = PromptBuilder().build_repository_prompt("CTX", STANDARDS)
    assert "{{" not in prompt                      # all placeholders substituted
    assert "STRICT KNOWLEDGE-BASE EVALUATION" in prompt
    assert "CTX" in prompt
    assert "OWASP — A03: Injection" in prompt


def test_reference_mode_injects_lenient_directive(monkeypatch):
    monkeypatch.setenv("STRICT_KNOWLEDGE_BASE", "false")
    prompt = PromptBuilder().build_repository_prompt("CTX", STANDARDS)
    assert "REFERENCE MODE" in prompt
    assert "STRICT KNOWLEDGE-BASE EVALUATION" not in prompt


def test_directive_loaded_from_resource_file(monkeypatch):
    # The directive text is now dynamic (loaded from resources/prompts/),
    # not hardcoded in Python.
    monkeypatch.setenv("STRICT_KNOWLEDGE_BASE", "true")
    assert "STRICT KNOWLEDGE-BASE EVALUATION" in PromptBuilder().directive()
    monkeypatch.setenv("STRICT_KNOWLEDGE_BASE", "false")
    assert "REFERENCE MODE" in PromptBuilder().directive()


def test_build_module_review_prompt_includes_code_and_standards(monkeypatch):
    monkeypatch.setenv("STRICT_KNOWLEDGE_BASE", "true")
    prompt = PromptBuilder().build_module_review_prompt(
        module_name="authentication",
        focus_areas=["Security"],
        code="--- auth/login.py ---\ndef verify(): ...",
        standards=STANDARDS,
    )
    assert "{{" not in prompt
    assert "authentication" in prompt
    assert "Focus areas: Security" in prompt
    assert "def verify()" in prompt                       # the real code is present
    assert "OWASP — A03: Injection" in prompt
    assert "STRICT KNOWLEDGE-BASE EVALUATION" in prompt


def test_build_final_report_prompt_includes_summaries_and_coverage():
    prompt = PromptBuilder().build_final_report_prompt(
        repository="demo (https://github.com/o/demo)",
        summaries="### Module: authentication\nLooks fine.",
        coverage="Reviewed 3 of 10 Python files (30%).",
    )
    assert "{{" not in prompt
    assert "demo (https://github.com/o/demo)" in prompt
    assert "### Module: authentication" in prompt
    assert "Reviewed 3 of 10 Python files (30%)." in prompt
    assert "# Repository Audit" in prompt
