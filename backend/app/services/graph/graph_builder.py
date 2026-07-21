from app.models.repository import Repository
from app.services.graph.graph_service import GraphService


class GraphBuilder:

    def __init__(self):
        self.graph = GraphService()

    def build(self, repository: Repository):

        self.graph.create_constraints()
        self.graph.clear_database()

        self.graph.create_node(
            "Repository",
            {
                "id": repository.github_url,
                "name": repository.name,
                "github_url": repository.github_url
            }
        )

        self._create_nodes(repository)
        self._create_calls(repository)
        self._create_inheritance(repository)
        self._create_imports(repository)

        #self.graph.close()

    def _create_nodes(self, repository: Repository):

        for python_file in repository.files:

            self.graph.create_node(
                "PythonFile",
                {
                    "id": python_file.id,
                    "name": python_file.name,
                    "relative_path": python_file.relative_path
                }
            )

            self.graph.create_relationship(
                "Repository",
                repository.github_url,
                "CONTAINS",
                "PythonFile",
                python_file.id
            )

            for python_class in python_file.classes:

                self.graph.create_node(
                    "PythonClass",
                    {
                        "id": python_class.id,
                        "name": python_class.name,
                        "line_number": python_class.line_number
                    }
                )

                self.graph.create_relationship(
                    "PythonFile",
                    python_file.id,
                    "DECLARES",
                    "PythonClass",
                    python_class.id
                )

                for method in python_class.methods:

                    self.graph.create_node(
                        "PythonFunction",
                        {
                            "id": method.id,
                            "name": method.name,
                            "line_number": method.line_number
                        }
                    )

                    self.graph.create_relationship(
                        "PythonClass",
                        python_class.id,
                        "DECLARES",
                        "PythonFunction",
                        method.id
                    )

            for function in python_file.functions:

                self.graph.create_node(
                    "PythonFunction",
                    {
                        "id": function.id,
                        "name": function.name,
                        "line_number": function.line_number
                    }
                )

                self.graph.create_relationship(
                    "PythonFile",
                    python_file.id,
                    "DECLARES",
                    "PythonFunction",
                    function.id
                )

    def _create_calls(self, repository: Repository):

        functions_by_name = {}

        for python_file in repository.files:

            for python_class in python_file.classes:

                for method in python_class.methods:

                    functions_by_name.setdefault(
                        method.name,
                        []
                    ).append(method)

            for function in python_file.functions:

                functions_by_name.setdefault(
                    function.name,
                    []
                ).append(function)

        for python_file in repository.files:

            for python_class in python_file.classes:

                for method in python_class.methods:

                    for call in method.calls:

                        for target in functions_by_name.get(call.name, []):

                            self.graph.create_relationship(
                                "PythonFunction",
                                method.id,
                                "CALLS",
                                "PythonFunction",
                                target.id
                            )

            for function in python_file.functions:

                for call in function.calls:

                    for target in functions_by_name.get(call.name, []):

                        self.graph.create_relationship(
                            "PythonFunction",
                            function.id,
                            "CALLS",
                            "PythonFunction",
                            target.id
                        )

    def _create_inheritance(self, repository: Repository):

        classes_by_name = {}

        for python_file in repository.files:

            for python_class in python_file.classes:

                classes_by_name.setdefault(
                    python_class.name,
                    []
                ).append(python_class)

        for python_file in repository.files:

            for python_class in python_file.classes:

                for base in python_class.base_classes:

                    for target in classes_by_name.get(base, []):

                        self.graph.create_relationship(
                            "PythonClass",
                            python_class.id,
                            "INHERITS_FROM",
                            "PythonClass",
                            target.id
                        )

    def _create_imports(self, repository: Repository):

        files_by_module = {}

        for python_file in repository.files:

            module = python_file.relative_path

            module = module.replace("\\", "/")
            module = module.replace("/", ".")

            if module.endswith(".py"):
                module = module[:-3]

            files_by_module[module] = python_file

        for python_file in repository.files:

            for imp in python_file.imports:

                parts = imp.module.split(".")

                if len(parts) > 1:
                    module = ".".join(parts[:-1])
                else:
                    module = parts[0]

                target = files_by_module.get(module)

                if target:

                    self.graph.create_relationship(
                        "PythonFile",
                        python_file.id,
                        "IMPORTS",
                        "PythonFile",
                        target.id
                    )