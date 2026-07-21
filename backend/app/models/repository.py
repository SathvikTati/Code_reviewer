from typing import List

from pydantic import BaseModel, Field

from app.models.python_file import PythonFile


class Repository(BaseModel):

    name: str

    github_url: str

    local_path: str

    files: List[PythonFile] = Field(default_factory=list)