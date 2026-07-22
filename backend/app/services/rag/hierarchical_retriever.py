from app.config.settings import settings
from app.services.rag.retriever import Retriever
from app.services.rag.module_grouper import ModuleGrouper
from app.services.rag.knowledge_retriever import KnowledgeRetriever


class HierarchicalRetriever:
    """Hierarchical GraphRAG retrieval.

    Instead of one flat query over the whole repository, this walks the
    structure repository -> module -> file -> classes/functions, and at the
    module level performs semantic retrieval against the knowledge base
    biased toward that module's relevant categories (e.g. an authentication
    module pulls Security standards, a database module pulls Security +
    Performance). This keeps only the applicable standards in context.
    """

    def __init__(self):
        self.retriever = Retriever()
        self.grouper = ModuleGrouper()
        self.knowledge_retriever = KnowledgeRetriever()
        self.module_k = settings.get("retrieval", "module_top_k", default=4)

    def retrieve(self) -> dict:

        rows = self.retriever.retrieve_repository_tree()
        modules = self.grouper.group(rows)

        result_modules = []

        for module in modules:

            files = self._collect_files(module)
            summary = self._summarize(files)

            query_text = f"{module.name} module.\n{summary}"

            standards = self.knowledge_retriever.search(
                query_text,
                k=self.module_k,
                categories=module.categories or None
            )

            result_modules.append(
                {
                    "name": module.name,
                    "categories": module.categories,
                    "files": files,
                    "standards": standards
                }
            )

        return {"modules": result_modules}

    def _collect_files(self, module) -> list[dict]:

        files = []

        for row in module.files:
            file = row.get("file", {})
            classes = [c for c in row.get("classes", []) if c]
            functions = [f for f in row.get("functions", []) if f]

            files.append(
                {
                    "relative_path": file.get("relative_path", ""),
                    "classes": classes,
                    "functions": functions
                }
            )

        return files

    def _summarize(self, files: list[dict]) -> str:

        lines = []

        for file in files:
            line = file["relative_path"]
            if file["classes"]:
                line += " | classes: " + ", ".join(file["classes"])
            if file["functions"]:
                line += " | functions: " + ", ".join(file["functions"])
            lines.append(line)

        return "\n".join(lines)
