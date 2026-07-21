from pathlib import Path

from app.models.repository import Repository
from app.models.python_file import PythonFile


class RepositoryScanner:

    def scan(self, repository: Repository) -> Repository:

        repo_path = Path(repository.local_path)

        for path in repo_path.rglob("*.py"):

            relative_path = str(path.relative_to(repo_path))

            repository.files.append(
                PythonFile(
                    id=relative_path,
                    name=path.name,
                    relative_path=relative_path,
                    absolute_path=str(path.resolve()),
                    size=path.stat().st_size
                )
            )

        return repository