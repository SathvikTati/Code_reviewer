import json

from app.config.settings import Settings


def _make_resources(tmp_path):
    (tmp_path / "config.json").write_text(json.dumps({
        "categories": ["Security", "Testing"],
        "retrieval": {"module_top_k": 3},
    }))
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "greet.md").write_text("Hello {{user}}, you are {{role}}.")
    return tmp_path


def test_nested_get_and_default(tmp_path, monkeypatch):
    monkeypatch.setenv("RESOURCES_DIR", str(_make_resources(tmp_path)))
    s = Settings()

    assert s.get("categories") == ["Security", "Testing"]
    assert s.get("retrieval", "module_top_k") == 3
    assert s.get("retrieval", "missing", default=7) == 7
    assert s.get("nope", default="x") == "x"


def test_render_prompt_substitutes_tokens(tmp_path, monkeypatch):
    monkeypatch.setenv("RESOURCES_DIR", str(_make_resources(tmp_path)))
    s = Settings()

    out = s.render_prompt("greet", user="Ada", role="auditor")
    assert out == "Hello Ada, you are auditor."
    assert "{{" not in out


def test_resources_dir_override_points_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("RESOURCES_DIR", str(_make_resources(tmp_path)))
    s = Settings()
    assert s.config_path == tmp_path / "config.json"
    assert s.knowledge_base_dir == tmp_path / "knowledge_base"
