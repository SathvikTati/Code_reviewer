import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from git import Repo

from app.models.repository import Repository


class CloneService:

    def __init__(self):
        # Clone OUTSIDE the backend directory so uvicorn's --reload watcher
        # doesn't detect the cloned files and restart the server mid-request.
        # Override with CLONE_DIR if you want the clones somewhere specific.
        override = os.getenv("CLONE_DIR")
        if override:
            self.base_dir = Path(override)
        else:
            self.base_dir = Path(tempfile.gettempdir()) / "code_reviewer_repos"

    def clone_repository(self, repo_url: str) -> Repository:
        """Clones a remote Git repository into a unique temporary directory."""

        repo_name = repo_url.rstrip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clone_path = self.base_dir / f"{repo_name}_{timestamp}"

        clone_path.parent.mkdir(parents=True, exist_ok=True)

        Repo.clone_from(repo_url, clone_path)

        return Repository(
                name=repo_name,
                github_url=repo_url,
                local_path=str(clone_path)
            )

    def delete_repository(self, repo_path):
        """Safely removes the local repository directory."""
        path = Path(repo_path)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
