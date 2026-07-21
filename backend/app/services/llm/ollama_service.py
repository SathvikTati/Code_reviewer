import os

from dotenv import load_dotenv
from ollama import Client

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

        response = self.client.generate(
            model=self.model,
            prompt=prompt
        )

        return response["response"]