from pathlib import Path

from app.config.settings import settings
from app.services.github.clone_service import CloneService
from app.services.scanner.scanner_service import RepositoryScanner
from app.services.parser.ParserService import ParserService
from app.services.graph.graph_builder import GraphBuilder

from app.services.builders.prompt_builder import PromptBuilder
from app.services.rag.hierarchical_retriever import HierarchicalRetriever
from app.services.llm.factory import create_llm_service
from app.telemetry import tracing
from app.telemetry import usage


class ReviewService:
    """Two-phase (map-reduce) code review:

    1. MAP    — for each logical module, send its ACTUAL source code plus the
                coding standards retrieved for it to the LLM, and get a concise
                per-module review.
    2. REDUCE — send all module reviews to the LLM once more to produce the
                final consolidated repository audit.
    """

    def __init__(self):

        self.clone_service = CloneService()
        self.scanner_service = RepositoryScanner()
        self.parser_service = ParserService()
        self.graph_builder = GraphBuilder()

        self.hierarchical_retriever = HierarchicalRetriever()
        self.prompt_builder = PromptBuilder()
        self.llm_service = create_llm_service()

    def analyze_repository(self, github_url: str) -> dict:

        repository = None
        collector = usage.start()

        try:
            with tracing.span(
                "analyze_repository",
                attributes={tracing.INPUT_VALUE: github_url},
            ) as root_span:

                with tracing.span("clone"):
                    repository = self.clone_service.clone_repository(github_url)

                with tracing.span("scan"):
                    repository = self.scanner_service.scan(repository)
                    file_count = len(repository.files)

                with tracing.span("parse", attributes={"repo.file_count": file_count}):
                    repository = self.parser_service.parse(repository)

                with tracing.span("build_graph"):
                    self.graph_builder.build(repository)

                # Group files into modules + retrieve KB standards per module.
                with tracing.span("hierarchical_retrieval", kind=tracing.KIND_RETRIEVER):
                    hierarchy = self.hierarchical_retriever.retrieve()

                # Map source files (with code on disk) by relative path.
                path_map = {
                    f.relative_path: f.absolute_path for f in repository.files
                }

                # --- Phase 1 (MAP): per-module code reviews ---
                module_reviews = []
                total_files = len(repository.files)
                reviewed_files = truncated_files = skipped_files = 0

                with tracing.span("module_reviews"):
                    for module in hierarchy.get("modules", []):
                        code, included, truncated, skipped = self._collect_module_code(
                            module, path_map
                        )
                        reviewed_files += included
                        truncated_files += truncated
                        skipped_files += skipped
                        if not code:
                            continue

                        prompt = self.prompt_builder.build_module_review_prompt(
                            module_name=module["name"],
                            focus_areas=module.get("categories", []),
                            code=code,
                            standards=module.get("standards", []),
                        )

                        with tracing.span(
                            f"module_review:{module['name']}",
                            attributes={
                                "module.files_included": included,
                                "module.files_truncated": truncated,
                                "module.files_skipped": skipped,
                            },
                        ):
                            summary = self.llm_service.generate(prompt)

                        module_reviews.append(
                            {"module": module["name"], "summary": summary}
                        )

                coverage = self._format_coverage(
                    total_files, reviewed_files, truncated_files,
                    skipped_files, len(module_reviews),
                )

                # --- Phase 2 (REDUCE): consolidate into the final report ---
                with tracing.span("final_report"):
                    summaries_text = self._format_summaries(module_reviews)
                    final_prompt = self.prompt_builder.build_final_report_prompt(
                        repository=f"{repository.name} ({repository.github_url})",
                        summaries=summaries_text,
                        coverage=coverage,
                    )
                    report = self.llm_service.generate(final_prompt)

                if root_span is not None:
                    root_span.set_attribute(
                        tracing.LLM_TOKEN_TOTAL, collector.total_tokens
                    )
                    root_span.set_attribute("review.modules", len(module_reviews))
                    root_span.set_attribute("review.files_reviewed", reviewed_files)
                    root_span.set_attribute("review.files_total", total_files)

                return {
                    "report": report,
                    "usage": collector.to_dict(),
                    "modules": [r["module"] for r in module_reviews],
                    "coverage": {
                        "files_total": total_files,
                        "files_reviewed": reviewed_files,
                        "files_truncated": truncated_files,
                        "files_skipped": skipped_files,
                    },
                }

        finally:
            # Remove the cloned repo (no user code lingers on the server) and
            # push buffered spans to Phoenix immediately.
            if repository is not None:
                self.clone_service.delete_repository(repository.local_path)
            tracing.flush()

    def _collect_module_code(self, module: dict, path_map: dict) -> tuple[str, int, int, int]:
        """Reads the actual source of a module's files from disk, capped by the
        review.* limits. Returns
        (code_text, files_included, files_truncated, files_skipped)."""

        max_file = settings.get("review", "max_file_chars", default=3000)
        max_module = settings.get("review", "max_module_chars", default=12000)
        max_files = settings.get("review", "max_files_per_module", default=40)

        files = module.get("files", [])
        parts, total, included, truncated, skipped = [], 0, 0, 0, 0

        for file in files[:max_files]:
            rel = file.get("relative_path", "")
            abs_path = path_map.get(rel)
            if not abs_path:
                continue

            try:
                code = Path(abs_path).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            if len(code) > max_file:
                code = code[:max_file] + "\n# … (truncated)"
                truncated += 1

            block = f"--- {rel} ---\n{code}"
            if total + len(block) > max_module and parts:
                skipped += 1
                continue

            parts.append(block)
            total += len(block)
            included += 1

        skipped += max(0, len(files) - max_files)
        return "\n\n".join(parts), included, truncated, skipped

    def _format_coverage(
        self, total: int, reviewed: int, truncated: int, skipped: int, modules: int
    ) -> str:
        """A one-line, honest statement of how much of the repo was reviewed."""
        pct = round(100 * reviewed / total) if total else 0
        note = (
            f"Reviewed {reviewed} of {total} Python files ({pct}%) across "
            f"{modules} module(s)."
        )
        if truncated:
            note += f" {truncated} file(s) were truncated to fit the code budget."
        if skipped:
            note += f" {skipped} file(s) were skipped (over the per-module limit)."
        note += " Findings reflect the reviewed code only."
        return note

    def _format_summaries(self, module_reviews: list[dict]) -> str:
        if not module_reviews:
            return "No module reviews were produced (the repository has no analyzable Python files)."
        blocks = [
            f"### Module: {r['module']}\n{r['summary']}"
            for r in module_reviews
        ]
        return "\n\n".join(blocks)
