from types import SimpleNamespace

from app.telemetry import tracing


def test_span_is_noop_when_tracer_disabled():
    # With PHOENIX_ENABLED=false (conftest), setup was never called -> _tracer is None.
    assert tracing.get_tracer() is None
    with tracing.span("anything", kind=tracing.KIND_LLM, attributes={"x": 1}) as s:
        assert s is None  # no-op span yields None and does not raise


def test_token_counts_from_dict_and_object():
    # dict-style (older ollama responses)
    assert tracing.token_counts({"prompt_eval_count": 7, "eval_count": 3}) == (7, 3)
    # object-style
    obj = SimpleNamespace(prompt_eval_count=4, eval_count=6)
    assert tracing.token_counts(obj) == (4, 6)
    # missing fields default to 0
    assert tracing.token_counts({}) == (0, 0)


def test_set_token_counts_tolerates_none_span():
    # Should be a no-op, not an error, when there's no active span.
    tracing.set_token_counts(None, 10, 5)


def test_flush_is_safe_when_disabled():
    tracing.flush()  # no tracer -> no-op
