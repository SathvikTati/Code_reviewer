from app.services.graph.graph_service import GraphService


class Retriever:

    def __init__(self):
        self.graph = GraphService()

    def retrieve_functions(self):

        query = """

        MATCH (f:PythonFunction)

        RETURN f

        """

        return self.graph.run_query(query)

    def get_functions(self):

        query = """
        MATCH (f:PythonFunction)
        RETURN f
        """

        return self.graph.run_query(query)

    def retrieve_function(
        self,
        name: str
    ):

        query = """

        MATCH (f:PythonFunction {name:$name})

        OPTIONAL MATCH (caller:PythonFunction)-[:CALLS]->(f)
        OPTIONAL MATCH (f)-[:CALLS]->(callee:PythonFunction)

        OPTIONAL MATCH (c:PythonClass)-[:DECLARES]->(f)

        OPTIONAL MATCH (file1:PythonFile)-[:DECLARES]->(f)

        OPTIONAL MATCH (file2:PythonFile)-[:DECLARES]->(c)

        RETURN
            f,
            collect(DISTINCT caller) AS callers,
            collect(DISTINCT callee) AS callees,
            c,
            coalesce(file1, file2) AS file

        """

        return self.graph.run_query(
            query,
            {
                "name": name
            }
        )
    def retrieve_class(
        self,
        name: str
    ):

        query = """

        MATCH (c:PythonClass {name:$name})

        OPTIONAL MATCH (c)-[:DECLARES]->(m:PythonFunction)

        OPTIONAL MATCH (c)-[:INHERITS_FROM]->(base:PythonClass)

        OPTIONAL MATCH (child:PythonClass)-[:INHERITS_FROM]->(c)

        OPTIONAL MATCH (file:PythonFile)-[:DECLARES]->(c)

        RETURN
            c,
            collect(DISTINCT m) AS methods,
            collect(DISTINCT base) AS base_classes,
            collect(DISTINCT child) AS subclasses,
            file

        """

        return self.graph.run_query(
            query,
            {
                "name": name
            }
        )
    
    def retrieve_file(
        self,
        relative_path: str
    ):

        query = """

        MATCH (file:PythonFile {relative_path:$relative_path})

        OPTIONAL MATCH (file)-[:DECLARES]->(c:PythonClass)

        OPTIONAL MATCH (file)-[:DECLARES]->(f:PythonFunction)

        OPTIONAL MATCH (file)-[:IMPORTS]->(imported:PythonFile)

        OPTIONAL MATCH (importer:PythonFile)-[:IMPORTS]->(file)

        RETURN
            file,
            collect(DISTINCT c) AS classes,
            collect(DISTINCT f) AS functions,
            collect(DISTINCT imported) AS imports,
            collect(DISTINCT importer) AS imported_by

        """

        return self.graph.run_query(
            query,
            {
                "relative_path": relative_path
            }
        )
    def retrieve_repository(self):

        query = """

        MATCH (r:Repository)

        OPTIONAL MATCH (r)-[:CONTAINS]->(file:PythonFile)

        OPTIONAL MATCH (file)-[:DECLARES]->(c:PythonClass)

        OPTIONAL MATCH (file)-[:DECLARES]->(f:PythonFunction)

        RETURN
            r,
            collect(DISTINCT file) AS files,
            collect(DISTINCT c) AS classes,
            collect(DISTINCT f) AS functions

        """

        return self.graph.run_query(query)