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