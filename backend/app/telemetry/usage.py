"""Per-request token-usage accounting.

A UsageCollector is stashed in a ContextVar at the start of an analysis; the
Ollama and embedding services add to it as they run, and the review service
reads the totals to return alongside the report. Because a single analysis
runs synchronously in one thread/context, the ContextVar is visible to every
call in the chain without threading a collector object through each layer.
"""

import contextvars

_current: contextvars.ContextVar = contextvars.ContextVar(
    "token_usage_collector", default=None
)


class UsageCollector:

    def __init__(self):
        self.llm_calls = 0
        self.embedding_calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def add_llm(self, prompt_tokens: int, completion_tokens: int):
        self.llm_calls += 1
        self.prompt_tokens += prompt_tokens or 0
        self.completion_tokens += completion_tokens or 0

    def add_embedding(self):
        self.embedding_calls += 1

    def to_dict(self) -> dict:
        return {
            "llm_calls": self.llm_calls,
            "embedding_calls": self.embedding_calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


def start() -> UsageCollector:
    """Begins a fresh usage scope for the current context."""
    collector = UsageCollector()
    _current.set(collector)
    return collector


def current() -> UsageCollector | None:
    return _current.get()


def record_llm(prompt_tokens: int, completion_tokens: int):
    collector = _current.get()
    if collector is not None:
        collector.add_llm(prompt_tokens, completion_tokens)


def record_embedding():
    collector = _current.get()
    if collector is not None:
        collector.add_embedding()
