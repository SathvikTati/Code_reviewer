from neo4j import GraphDatabase


class GraphService:

    def __init__(self):

        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )

    def close(self):
        self.driver.close()

    def create_repository(self, name: str, github_url: str):

        query = """
        CREATE (r:Repository {
            name: $name,
            github_url: $github_url
        })
        """

        with self.driver.session() as session:

            session.run(
                query,
                name=name,
                github_url=github_url
            )


graph = GraphService()

graph.create_repository(
    "flask",
    "https://github.com/pallets/flask"
)

graph.close()