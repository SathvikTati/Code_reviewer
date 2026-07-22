"""Observability via Arize Phoenix.

Manually instruments the pipeline (we call Ollama directly, not through an
auto-instrumented client) using OpenInference semantic conventions, so Phoenix
shows LLM/embedding/retriever spans with token counts and timing.

Everything here is no-op safe: if Phoenix is disabled or the collector is not
running, spans quietly do nothing and the app keeps working.
"""

import os
from contextlib import contextmanager

from dotenv import load_dotenv

load_dotenv()

# OpenInference attribute keys (fall back to raw strings if unavailable).
try:
    from openinference.semconv.trace import (
        SpanAttributes,
        OpenInferenceSpanKindValues,
    )

    SPAN_KIND = SpanAttributes.OPENINFERENCE_SPAN_KIND
    LLM_MODEL_NAME = SpanAttributes.LLM_MODEL_NAME
    LLM_TOKEN_PROMPT = SpanAttributes.LLM_TOKEN_COUNT_PROMPT
    LLM_TOKEN_COMPLETION = SpanAttributes.LLM_TOKEN_COUNT_COMPLETION
    LLM_TOKEN_TOTAL = SpanAttributes.LLM_TOKEN_COUNT_TOTAL
    INPUT_VALUE = SpanAttributes.INPUT_VALUE
    OUTPUT_VALUE = SpanAttributes.OUTPUT_VALUE
    EMBEDDING_MODEL_NAME = SpanAttributes.EMBEDDING_MODEL_NAME

    KIND_LLM = OpenInferenceSpanKindValues.LLM.value
    KIND_EMBEDDING = OpenInferenceSpanKindValues.EMBEDDING.value
    KIND_RETRIEVER = OpenInferenceSpanKindValues.RETRIEVER.value
    KIND_CHAIN = OpenInferenceSpanKindValues.CHAIN.value
except Exception:  # pragma: no cover
    SPAN_KIND = "openinference.span.kind"
    LLM_MODEL_NAME = "llm.model_name"
    LLM_TOKEN_PROMPT = "llm.token_count.prompt"
    LLM_TOKEN_COMPLETION = "llm.token_count.completion"
    LLM_TOKEN_TOTAL = "llm.token_count.total"
    INPUT_VALUE = "input.value"
    OUTPUT_VALUE = "output.value"
    EMBEDDING_MODEL_NAME = "embedding.model_name"
    KIND_LLM, KIND_EMBEDDING, KIND_RETRIEVER, KIND_CHAIN = (
        "LLM", "EMBEDDING", "RETRIEVER", "CHAIN"
    )


_tracer = None
_initialized = False


def _enabled() -> bool:
    return os.getenv("PHOENIX_ENABLED", "true").lower() == "true"


def setup_tracing():
    """Registers the Phoenix OTEL tracer provider. Call once at startup.

    Optionally launches the Phoenix UI in-process when PHOENIX_LAUNCH=true;
    otherwise it exports to a Phoenix server you run separately
    (`phoenix serve`, default http://localhost:6006).
    """

    global _tracer, _initialized

    if _initialized:
        return _tracer

    _initialized = True

    if not _enabled():
        print("[telemetry] Phoenix disabled (PHOENIX_ENABLED=false).")
        return None

    launch = os.getenv("PHOENIX_LAUNCH", "false").lower() == "true"

    try:
        from phoenix.otel import register

        register_kwargs = {
            "project_name": os.getenv("PHOENIX_PROJECT", "code-review"),
            "auto_instrument": False,
            "batch": True,
        }

        if launch:
            # Launching the UI in-process: the collector endpoint must NOT be
            # set, or Phoenix thinks traces go elsewhere. Let register auto-
            # detect the in-process app.
            os.environ.pop("PHOENIX_COLLECTOR_ENDPOINT", None)
            import phoenix as px
            session = px.launch_app()
            print(f"[telemetry] Phoenix UI launched at {session.url}")
        else:
            # Export to a Phoenix server you run separately (`phoenix serve`).
            register_kwargs["endpoint"] = os.getenv(
                "PHOENIX_COLLECTOR_ENDPOINT",
                "http://localhost:6006/v1/traces",
            )

        provider = register(**register_kwargs)

        _tracer = provider.get_tracer("code-review")
        print("[telemetry] Phoenix tracing enabled.")
    except Exception as error:  # pragma: no cover
        print(f"[telemetry] Phoenix tracing unavailable: {error}")
        _tracer = None

    return _tracer


def flush():
    """Forces any buffered spans to export immediately. Call after a unit of
    work (e.g. one analysis) so traces show up in Phoenix without waiting for
    the batch interval."""
    if _tracer is None:
        return
    try:
        from opentelemetry import trace
        trace.get_tracer_provider().force_flush()
    except Exception:  # pragma: no cover
        pass


def get_tracer():
    return _tracer


@contextmanager
def span(name: str, kind: str = KIND_CHAIN, attributes: dict | None = None):
    """Context manager for a span. No-op when tracing is off. Yields the span
    (or None) so callers can add attributes such as token counts."""

    if _tracer is None:
        yield None
        return

    with _tracer.start_as_current_span(name) as current:
        current.set_attribute(SPAN_KIND, kind)
        for key, value in (attributes or {}).items():
            if value is not None:
                current.set_attribute(key, value)
        yield current


def _field(response, key, default=None):
    """Reads a field from an Ollama response whether it is a dict or an
    object (the ollama client has returned both across versions)."""
    try:
        value = response[key]
    except (KeyError, TypeError, IndexError):
        value = getattr(response, key, default)
    return value if value is not None else default


def token_counts(response) -> tuple[int, int]:
    """Extracts (prompt_tokens, completion_tokens) from an Ollama response."""
    return (
        _field(response, "prompt_eval_count", 0),
        _field(response, "eval_count", 0),
    )


def set_token_counts(current, prompt_tokens: int, completion_tokens: int):
    """Sets LLM token-count attributes on a span from explicit numbers
    (e.g. an OpenAI usage object)."""
    if current is None:
        return
    prompt_tokens = prompt_tokens or 0
    completion_tokens = completion_tokens or 0
    current.set_attribute(LLM_TOKEN_PROMPT, prompt_tokens)
    current.set_attribute(LLM_TOKEN_COMPLETION, completion_tokens)
    current.set_attribute(LLM_TOKEN_TOTAL, prompt_tokens + completion_tokens)


def record_llm_usage(current, response):
    """Records Ollama token counts and timing on an LLM span."""
    if current is None:
        return

    prompt_tokens, completion_tokens = token_counts(response)

    current.set_attribute(LLM_TOKEN_PROMPT, prompt_tokens)
    current.set_attribute(LLM_TOKEN_COMPLETION, completion_tokens)
    current.set_attribute(LLM_TOKEN_TOTAL, prompt_tokens + completion_tokens)

    # Ollama durations are nanoseconds; expose milliseconds for readability.
    for field in (
        "total_duration",
        "load_duration",
        "prompt_eval_duration",
        "eval_duration",
    ):
        value = _field(response, field)
        if value is not None:
            current.set_attribute(f"ollama.{field}_ms", round(value / 1e6, 2))
