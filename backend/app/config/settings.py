import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central access point for externalized resources (the root `resources/`
    control panel): config.json, prompt templates, and the knowledge base.

    The resources directory can be overridden with the RESOURCES_DIR env var;
    otherwise it defaults to `<repo-root>/resources`.
    """

    def __init__(self):

        override = os.getenv("RESOURCES_DIR")

        if override:
            self.resources_dir = Path(override).resolve()
        else:
            # settings.py -> config -> app -> backend -> repo root
            repo_root = Path(__file__).resolve().parents[3]
            self.resources_dir = repo_root / "resources"

        self.config_path = self.resources_dir / "config.json"
        self.prompts_dir = self.resources_dir / "prompts"
        self.knowledge_base_dir = self.resources_dir / "knowledge_base"

        self._config = None
        self._prompt_cache: dict[str, str] = {}

    # -- config -------------------------------------------------------------

    @property
    def config(self) -> dict:
        if self._config is None:
            if not self.config_path.exists():
                raise FileNotFoundError(
                    f"Config file not found at {self.config_path}"
                )
            with open(self.config_path, "r", encoding="utf-8") as file:
                self._config = json.load(file) or {}
        return self._config

    def get(self, *keys, default=None):
        """Nested lookup, e.g. settings.get('retrieval', 'module_top_k')."""
        node = self.config
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    # -- prompts ------------------------------------------------------------

    def load_prompt(self, name: str) -> str:
        """Loads a prompt template by name (without extension) from prompts/."""
        if name in self._prompt_cache:
            return self._prompt_cache[name]

        path = self.prompts_dir / f"{name}.md"
        if not path.exists():
            raise FileNotFoundError(f"Prompt template not found: {path}")

        template = path.read_text(encoding="utf-8")
        self._prompt_cache[name] = template
        return template

    def render_prompt(self, name: str, **values) -> str:
        """Renders a prompt template, replacing {{token}} placeholders."""
        template = self.load_prompt(name)
        for key, value in values.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        return template


# Shared singleton.
settings = Settings()
