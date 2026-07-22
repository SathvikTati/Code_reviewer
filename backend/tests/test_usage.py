from app.telemetry import usage


def test_collector_accumulates():
    c = usage.UsageCollector()
    c.add_llm(30, 12)
    c.add_llm(10, 8)
    c.add_embedding()
    c.add_embedding()

    assert c.llm_calls == 2
    assert c.embedding_calls == 2
    assert c.prompt_tokens == 40
    assert c.completion_tokens == 20
    assert c.total_tokens == 60
    assert c.to_dict() == {
        "llm_calls": 2, "embedding_calls": 2,
        "prompt_tokens": 40, "completion_tokens": 20, "total_tokens": 60,
    }


def test_start_sets_current_scope_and_record_helpers():
    collector = usage.start()
    assert usage.current() is collector

    usage.record_llm(5, 5)
    usage.record_embedding()

    assert collector.total_tokens == 10
    assert collector.embedding_calls == 1


def test_record_helpers_are_safe_without_scope(monkeypatch):
    # Reset the context var so there's no active collector.
    monkeypatch.setattr(usage, "_current", usage.contextvars.ContextVar("x", default=None))
    # Should not raise even with no active collector.
    usage.record_llm(1, 1)
    usage.record_embedding()
