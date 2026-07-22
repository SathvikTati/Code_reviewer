from app.services.llm.factory import create_llm_service
from app.services.llm.ollama_service import OllamaService
from app.services.llm.openai_service import OpenAIService


def test_defaults_to_ollama(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert isinstance(create_llm_service(), OllamaService)


def test_selects_ollama(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    assert isinstance(create_llm_service(), OllamaService)


def test_selects_openai(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")   # construction only, no API call
    assert isinstance(create_llm_service(), OpenAIService)


def test_unknown_provider_falls_back_to_ollama(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "banana")
    assert isinstance(create_llm_service(), OllamaService)
