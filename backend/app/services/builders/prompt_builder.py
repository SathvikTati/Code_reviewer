import os

from app.config.settings import settings


def strict_knowledge_base_enabled() -> bool:
    """Reads the STRICT_KNOWLEDGE_BASE env var (default: on)."""
    return os.getenv("STRICT_KNOWLEDGE_BASE", "true").strip().lower() in (
        "1", "true", "yes", "on",
    )


class PromptBuilder:
    """Builds LLM prompts by rendering editable templates from
    resources/prompts/ — no prompt text is hardcoded here. Even the strict /
    reference evaluation directives are loaded from resources/prompts/."""

    def directive(self) -> str:
        """The evaluation-mode header, loaded dynamically from resources/prompts/
        (strict_directive.md or lenient_directive.md)."""
        name = "strict_directive" if strict_knowledge_base_enabled() else "lenient_directive"
        return settings.load_prompt(name).strip()

    def format_standards(self, standards: list[dict]) -> str:
        """Formats retrieved knowledge-base chunks into a readable block."""

        if not standards:
            return "No specific coding standards were retrieved."

        lines = []

        for item in standards:
            category = item.get("category", "General")
            title = item.get("title", item.get("source", ""))
            text = item.get("text", "")

            lines.append(f"[{category}] {title}")
            lines.append(text)
            lines.append("")

        return "\n".join(lines).strip()

    # -- Phase 1: per-module review (map) ----------------------------------

    def build_module_review_prompt(
        self,
        module_name: str,
        focus_areas: list[str],
        code: str,
        standards: list[dict] | None = None,
    ) -> str:

        return settings.render_prompt(
            "module_review",
            module_name=module_name,
            focus_areas=", ".join(focus_areas) if focus_areas else "General",
            code=code,
            standards=self.format_standards(standards or []),
            strict_directive=self.directive(),
        )

    # -- Phase 2: final consolidated report (reduce) -----------------------

    def build_final_report_prompt(
        self,
        repository: str,
        summaries: str,
        coverage: str = "",
    ) -> str:

        return settings.render_prompt(
            "final_report",
            repository=repository,
            summaries=summaries,
            coverage=coverage or "Coverage information unavailable.",
        )

    # -- Single-call report (legacy / structure-only) ----------------------

    def build_repository_prompt(
        self,
        context: str,
        standards: list[dict] | None = None
    ) -> str:

        return settings.render_prompt(
            "repository_report",
            context=context,
            standards=self.format_standards(standards or []),
            strict_directive=self.directive(),
        )

    def build_prompt(
        self,
        question: str,
        context: str,
        standards: list[dict] | None = None
    ) -> str:

        return settings.render_prompt(
            "qa",
            question=question,
            context=context,
            standards=self.format_standards(standards or [])
        )
