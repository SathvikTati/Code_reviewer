import os

from dotenv import load_dotenv

from app.services.llm.ollama_service import OllamaService
from app.services.llm.openai_service import OpenAIService

load_dotenv()


def create_llm_service():
    """Returns the LLM backend selected by the LLM_PROVIDER env var
    ('ollama' by default, or 'openai'). Both expose generate(prompt) -> str."""

    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

    if provider == "openai":
        return OpenAIService()

    return OllamaService()
