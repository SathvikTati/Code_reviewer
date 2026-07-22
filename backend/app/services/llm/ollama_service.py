import os

from dotenv import load_dotenv
from ollama import Client

from app.telemetry import tracing
from app.telemetry import usage

load_dotenv()


class OllamaService:

    def __init__(self):

        self.client = Client(
            host=os.getenv("OLLAMA_HOST")
        )

        self.model = os.getenv("OLLAMA_MODEL")

    def generate(
        self,
        prompt: str
    ) -> str:

        with tracing.span(
            "ollama.generate",
            kind=tracing.KIND_LLM,
            attributes={
                tracing.LLM_MODEL_NAME: self.model,
                tracing.INPUT_VALUE: prompt,
            },
        ) as current:

            response = self.client.generate(
                model=self.model,
                prompt=prompt
            )

            output = response["response"]

            prompt_tokens, completion_tokens = tracing.token_counts(response)
            usage.record_llm(prompt_tokens, completion_tokens)

            if current is not None:
                current.set_attribute(tracing.OUTPUT_VALUE, output)
                tracing.record_llm_usage(current, response)

            return output