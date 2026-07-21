class PromptBuilder:

    def build_prompt(self, question: str, context: str) -> str:
        return f"""
You are an expert Python code reviewer.

Use ONLY the provided repository context to answer the user's question.

Repository Context
------------------
{context}

User Question
-------------
{question}

Provide:
1. A clear answer.
2. Explain your reasoning.
3. Mention any potential issues or improvements if relevant.
""".strip()

    def build_repository_prompt(self, context: str) -> str:
        return f"""
You are an expert Python software architect.

Analyze the following repository.

Repository Context
------------------
{context}

Provide:

1. Project purpose
2. Overall architecture
3. Important modules
4. Design patterns
5. Code quality
6. Performance issues
7. Security issues
8. Refactoring suggestions
9. Overall summary
""".strip()