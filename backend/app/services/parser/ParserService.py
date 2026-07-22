import ast

from app.models.python_call import PythonCall
from app.models.repository import Repository
from app.models.python_class import PythonClass
from app.models.python_function import PythonFunction
from app.models.python_import import PythonImport
from app.models.python_parameter import PythonParameter


class ParserService:

    def parse(self, repository: Repository) -> Repository:

        for python_file in repository.files:

            # A single unparseable file (invalid syntax, Python 2, template
            # pseudo-code, bad encoding, ...) must not abort the whole
            # analysis — skip it and keep going.
            try:
                with open(python_file.absolute_path, "r", encoding="utf-8") as file:
                    code = file.read()

                tree = ast.parse(code)
            except (SyntaxError, ValueError, UnicodeDecodeError, OSError) as error:
                python_file.parse_error = str(error)
                print(
                    f"[parser] skipping {python_file.relative_path}: {error}"
                )
                continue

            python_file.imports.clear()
            python_file.classes.clear()
            python_file.functions.clear()

            for node in tree.body:

                if isinstance(node, ast.Import):

                    for alias in node.names:
                        python_file.imports.append(
                            PythonImport(
                                module=alias.name
                            )
                        )

                elif isinstance(node, ast.ImportFrom):

                    module = node.module or ""

                    for alias in node.names:
                        python_file.imports.append(
                            PythonImport(
                                module=f"{module}.{alias.name}"
                            )
                        )

                elif isinstance(node, ast.ClassDef):

                    python_class = PythonClass(
                        id=f"{python_file.relative_path}::{node.name}",
                        name=node.name,
                        line_number=node.lineno
                    )

                    for base in node.bases:

                        if isinstance(base, ast.Name):
                            python_class.base_classes.append(base.id)

                        elif isinstance(base, ast.Attribute):
                            python_class.base_classes.append(base.attr)

                    for item in node.body:

                        if isinstance(item, ast.FunctionDef):

                            method = PythonFunction(
                                id=f"{python_file.relative_path}::{node.name}::{item.name}",
                                name=item.name,
                                line_number=item.lineno
                            )

                            for decorator in item.decorator_list:

                                if isinstance(decorator, ast.Name):
                                    method.decorators.append(decorator.id)

                                elif isinstance(decorator, ast.Attribute):
                                    method.decorators.append(decorator.attr)

                            for arg in item.args.args:

                                method.parameters.append(
                                    PythonParameter(
                                        name=arg.arg
                                    )
                                )

                            for child in ast.walk(item):

                                if isinstance(child, ast.Call):

                                    if isinstance(child.func, ast.Name):

                                        method.calls.append(
                                            PythonCall(
                                                name=child.func.id
                                            )
                                        )

                                    elif isinstance(child.func, ast.Attribute):

                                        method.calls.append(
                                            PythonCall(
                                                name=child.func.attr
                                            )
                                        )

                            python_class.methods.append(method)

                    python_file.classes.append(python_class)

                elif isinstance(node, ast.FunctionDef):

                    function = PythonFunction(
                        id=f"{python_file.relative_path}::{node.name}",
                        name=node.name,
                        line_number=node.lineno
                    )

                    for decorator in node.decorator_list:

                        if isinstance(decorator, ast.Name):
                            function.decorators.append(decorator.id)

                        elif isinstance(decorator, ast.Attribute):
                            function.decorators.append(decorator.attr)

                    for arg in node.args.args:

                        function.parameters.append(
                            PythonParameter(
                                name=arg.arg
                            )
                        )

                    for child in ast.walk(node):

                        if isinstance(child, ast.Call):

                            if isinstance(child.func, ast.Name):

                                function.calls.append(
                                    PythonCall(
                                        name=child.func.id
                                    )
                                )

                            elif isinstance(child.func, ast.Attribute):

                                function.calls.append(
                                    PythonCall(
                                        name=child.func.attr
                                    )
                                )

                    python_file.functions.append(function)

        return repository