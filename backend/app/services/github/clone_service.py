from datetime import datetime
from pathlib import Path
import shutil
from git import Repo

from app.models.repository import Repository


class CloneService:

    def clone_repository(self, repo_url: str) -> Repository:
        """Clones a remote Git repository into a unique temporary directory."""

        repo_name = repo_url.rstrip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clone_path = Path("temp") / f"{repo_name}_{timestamp}"

        clone_path.parent.mkdir(exist_ok=True)

        Repo.clone_from(repo_url, clone_path)

        return Repository(
                name=repo_name,
                github_url=repo_url,
                local_path=str(clone_path)
            )

    def delete_repository(self, repo_path: Path):
        """Safely removes the local repository directory."""
        if repo_path.exists():
            shutil.rmtree(repo_path)