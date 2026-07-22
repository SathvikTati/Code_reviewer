import pytest

from app.services.rag.module_grouper import ModuleGrouper, _singular, _tokenize


@pytest.fixture
def grouper():
    return ModuleGrouper()


@pytest.mark.parametrize("path,expected", [
    ("app/auth/login.py", "authentication"),
    ("authentication.py", "authentication"),
    ("api/user_controller.py", "api"),
    ("api/views.py", "api"),
    ("services/review/review_service.py", "services"),
    ("models/user.py", "database"),
    ("config/settings.py", "configuration"),
    ("tests/test_x.py", "testing"),
    ("utils/helpers.py", "utilities"),
    # False positives that the whole-word matcher must NOT map to authentication:
    ("nlp/tokenizer.py", "general"),
    ("nlp/tokens.py", "general"),
    ("blog/author.py", "general"),
    # No signal -> catch-all:
    ("random_file.py", "general"),
])
def test_match_assigns_expected_module(grouper, path, expected):
    assert grouper._match(path)["name"] == expected


def test_singularization():
    assert _singular("models") == "model"
    assert _singular("services") == "service"
    assert _singular("class") == "class"      # 'ss' is not stripped
    assert _singular("api") == "api"


def test_tokenize_splits_on_separators_and_case():
    assert _tokenize("services/review/review_service.py") == [
        "services", "review", "review", "service", "py"
    ]


def test_group_buckets_files_and_preserves_categories(grouper):
    rows = [
        {"file": {"relative_path": "app/auth/login.py"}},
        {"file": {"relative_path": "app/utils/text.py"}},
        {"file": {"relative_path": "app/auth/tokens_helper.py"}},
    ]
    modules = grouper.group(rows)
    by_name = {m.name: m for m in modules}

    assert "authentication" in by_name
    assert "utilities" in by_name
    assert by_name["authentication"].categories == ["Security"]
    # login.py grouped under authentication
    paths = [f["file"]["relative_path"] for f in by_name["authentication"].files]
    assert "app/auth/login.py" in paths
