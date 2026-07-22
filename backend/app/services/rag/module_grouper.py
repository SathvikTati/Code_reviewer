import re

from app.config.settings import settings


def _tokenize(path: str) -> list[str]:
    """Splits a path into lowercase word tokens (on separators and digits),
    e.g. 'services/review/review_service.py' -> [services, review, service, py].
    Token-based matching avoids false positives like 'view' matching 'review'."""
    return [t for t in re.split(r"[^a-z0-9]+", path.lower()) if t]


def _singular(word: str) -> str:
    """Naive singularization: drops a single trailing plural 's' so that
    'models' == 'model' and 'services' == 'service', without prefix matching
    (which wrongly made 'token' match 'tokenizer' and 'auth' match 'author').
    Skips 'ss' endings ('class' stays 'class')."""
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


class Module:

    def __init__(self, name: str, categories: list[str]):
        self.name = name
        self.categories = categories
        self.files: list[dict] = []  # rows from retrieve_repository_tree


class ModuleGrouper:
    """Groups repository files into logical modules using the config-driven
    rules in resources/config.json. Each file is assigned to the first module
    whose keywords match its relative path (case-insensitive). The catch-all
    module (empty keywords, kept last) absorbs the rest."""

    def __init__(self):
        self.module_defs = settings.get("modules", default=[])

    def _match(self, relative_path: str) -> dict:
        # Match on whole words (singularized), not prefixes. 'tokenizer' no
        # longer matches 'token', 'author' no longer matches 'auth'.
        tokens = {_singular(t) for t in _tokenize(relative_path)}

        for module_def in self.module_defs:
            keywords = module_def.get("keywords", [])
            if not keywords:
                # Catch-all fallback.
                return module_def
            for keyword in keywords:
                if _singular(keyword.lower()) in tokens:
                    return module_def

        # No fallback configured — synthesize one.
        return {"name": "general", "categories": []}

    def group(self, file_rows: list[dict]) -> list[Module]:
        """file_rows: output of Retriever.retrieve_repository_tree()."""

        modules: dict[str, Module] = {}
        order: list[str] = []

        for row in file_rows:
            file = row.get("file", {})
            relative_path = file.get("relative_path", "")

            module_def = self._match(relative_path)
            name = module_def.get("name", "general")

            if name not in modules:
                modules[name] = Module(
                    name=name,
                    categories=module_def.get("categories", [])
                )
                order.append(name)

            modules[name].files.append(row)

        return [modules[name] for name in order]
