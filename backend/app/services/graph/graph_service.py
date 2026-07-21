from neo4j import GraphDatabase
from dotenv import load_dotenv

import os

load_dotenv()


class GraphService:

    def __init__(self):

        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(
                os.getenv("NEO4J_USERNAME"),
                os.getenv("NEO4J_PASSWORD")
            )
        )

    def close(self):
        self.driver.close()

    def create_constraints(self):

        queries = [

            """
            CREATE CONSTRAINT repository_id
            IF NOT EXISTS
            FOR (n:Repository)
            REQUIRE n.id IS UNIQUE
            """,

            """
            CREATE CONSTRAINT python_file_id
            IF NOT EXISTS
            FOR (n:PythonFile)
            REQUIRE n.id IS UNIQUE
            """,

            """
            CREATE CONSTRAINT python_class_id
            IF NOT EXISTS
            FOR (n:PythonClass)
            REQUIRE n.id IS UNIQUE
            """,

            """
            CREATE CONSTRAINT python_function_id
            IF NOT EXISTS
            FOR (n:PythonFunction)
            REQUIRE n.id IS UNIQUE
            """

        ]

        with self.driver.session() as session:

            for query in queries:
                session.run(query)

    def clear_database(self):

        query = """
        MATCH (n)
        DETACH DELETE n
        """

        with self.driver.session() as session:
            session.run(query)

    def create_node(self, label: str, properties: dict):

        merge = f"MERGE (n:{label} {{id:$id}})"

        setters = []

        for key in properties.keys():

            if key != "id":
                setters.append(f"n.{key} = ${key}")

        query = merge

        if setters:

            query += "\nSET " + ", ".join(setters)

        with self.driver.session() as session:
            session.run(query, **properties)

    def create_relationship(
        self,
        from_label: str,
        from_id: str,
        relationship: str,
        to_label: str,
        to_id: str
    ):

        query = f"""
        MATCH (a:{from_label} {{id:$from_id}})
        MATCH (b:{to_label} {{id:$to_id}})

        MERGE (a)-[:{relationship}]->(b)
        """

        with self.driver.session() as session:

            session.run(
                query,
                from_id=from_id,
                to_id=to_id
            )

    def run_query(
        self,
        query: str,
        parameters: dict | None = None
    ):

        with self.driver.session() as session:

            result = session.run(
                query,
                parameters or {}
            )

            return [
                record.data()
                for record in result
            ]