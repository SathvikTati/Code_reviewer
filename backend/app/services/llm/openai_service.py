import os

from dotenv import load_dotenv
from openai import OpenAI

from app.telemetry import tracing
from app.telemetry import usage

load_dotenv()


class OpenAIService:
    """LLM backend using the OpenAI Chat Completions API. Same interface as
    OllamaService (generate(prompt) -> str) so the two are interchangeable."""

    def __init__(self):

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL") or None,
        )

        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate(
        self,
        prompt: str
    ) -> str:

        with tracing.span(
            "openai.generate",
            kind=tracing.KIND_LLM,
            attributes={
                tracing.LLM_MODEL_NAME: self.model,
                tracing.INPUT_VALUE: prompt,
            },
        ) as current:

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )

            output = response.choices[0].message.content or ""

            usage_obj = getattr(response, "usage", None)
            prompt_tokens = getattr(usage_obj, "prompt_tokens", 0) or 0
            completion_tokens = getattr(usage_obj, "completion_tokens", 0) or 0

            usage.record_llm(prompt_tokens, completion_tokens)

            if current is not None:
                current.set_attribute(tracing.OUTPUT_VALUE, output)
                tracing.set_token_counts(current, prompt_tokens, completion_tokens)

            return output
