class ContextBuilder:

    def _append_list(self, context: list, title: str, items: list, key: str = "name"):

        context.append(f"=== {title} ===")

        if items:
            for item in items:
                context.append(f"- {item[key]}")
        else:
            context.append("- None")

        context.append("")

    def build_function_context(
        self,
        result: list
    ) -> str:

        if not result:
            return "Function not found."

        data = result[0]

        function = data.get("f")
        callers = data.get("callers", [])
        callees = data.get("callees", [])
        python_class = data.get("c")
        python_file = data.get("file")

        parameters = function.get("parameters", [])
        decorators = function.get("decorators", [])
        source_code = function.get("source_code")

        context = []

        context.append("=== Function ===")
        context.append(f"Name: {function['name']}")
        context.append(f"Line: {function['line_number']}")

        if function.get("id"):
            context.append(f"ID: {function['id']}")

        context.append("")

        if python_class:
            context.append("=== Class ===")
            context.append(f"Name: {python_class['name']}")
            context.append("")

        if python_file:
            context.append("=== File ===")
            context.append(f"Path: {python_file['relative_path']}")
            context.append("")

        self._append_list(context, "Parameters", parameters)
        self._append_list(context, "Decorators", decorators)

        self._append_list(context, "Calls", callees)
        self._append_list(context, "Called By", callers)

        if source_code:
            context.append("=== Source Code ===")
            context.append(source_code)

        return "\n".join(context)
    
    def build_hierarchical_context(
        self,
        repository,
        hierarchy: dict
    ) -> str:
        """Formats the repository as modules -> files -> classes/functions,
        annotating each module with the coding-standard titles retrieved for
        it. Full standard text is provided separately (deduped)."""

        context = []

        context.append("=== Repository ===")
        context.append(f"Name: {repository.name}")
        context.append(f"GitHub URL: {repository.github_url}")
        context.append("")

        for module in hierarchy.get("modules", []):

            context.append(f"=== Module: {module['name']} ===")

            categories = module.get("categories") or []
            if categories:
                context.append(f"Focus areas: {', '.join(categories)}")

            files = module.get("files", [])
            context.append(f"Files ({len(files)}):")

            for file in files:
                context.append(f"- {file['relative_path']}")
                if file["classes"]:
                    context.append(f"    classes: {', '.join(file['classes'])}")
                if file["functions"]:
                    context.append(f"    functions: {', '.join(file['functions'])}")

            standards = module.get("standards", [])
            if standards:
                titles = [
                    f"[{s.get('category')}] {s.get('title')}"
                    for s in standards
                ]
                context.append("Applicable standards: " + "; ".join(titles))

            context.append("")

        return "\n".join(context)

    def merge_standards(self, hierarchy: dict) -> list[dict]:
        """Collects standards across all modules, de-duplicated by source+title,
        keeping the highest relevance score."""

        best: dict[tuple, dict] = {}

        for module in hierarchy.get("modules", []):
            for standard in module.get("standards", []):
                key = (standard.get("source"), standard.get("title"))
                score = standard.get("score", 0)
                if key not in best or score > best[key].get("score", 0):
                    best[key] = standard

        return sorted(
            best.values(),
            key=lambda s: s.get("score", 0),
            reverse=True
        )

    def build_repository_context(self, result: list) -> str:

        if not result:
            return "Repository not found."

        data = result[0]

        repository = data.get("r")
        files = data.get("files", [])
        classes = data.get("classes", [])
        functions = data.get("functions", [])

        context = []

        context.append("=== Repository ===")
        context.append(f"Name: {repository['name']}")
        context.append(f"GitHub URL: {repository['github_url']}")
        context.append("")

        self._append_list(context, "Files", files, "relative_path")
        self._append_list(context, "Classes", classes)
        self._append_list(context, "Functions", functions)

        return "\n".join(context)