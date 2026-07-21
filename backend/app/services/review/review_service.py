from app.services.github.clone_service import CloneService
from app.services.scanner.scanner_service import RepositoryScanner
from app.services.parser.ParserService import ParserService
from app.services.graph.graph_builder import GraphBuilder

from app.services.builders.context_builder import ContextBuilder
from app.services.builders.prompt_builder import PromptBuilder
from app.services.rag.retriever import Retriever
from app.services.llm.ollama_service import OllamaService


class ReviewService:

    def __init__(self):

        self.clone_service = CloneService()
        self.scanner_service = RepositoryScanner()
        self.parser_service = ParserService()
        self.graph_builder = GraphBuilder()

        self.retriever = Retriever()
        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()
        self.ollama_service = OllamaService()

    def analyze_repository(
        self,
        github_url: str
    ) -> str:

        repository = self.clone_service.clone_repository(github_url)

        repository = self.scanner_service.scan(repository)

        repository = self.parser_service.parse(repository)

        self.graph_builder.build(repository)

        result = self.retriever.retrieve_repository()

        context = self.context_builder.build_repository_context(result)

        prompt = self.prompt_builder.build_repository_prompt(context)

        return self.ollama_service.generate(prompt)