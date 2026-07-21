from typing import List

from pydantic import BaseModel, Field

from app.models.python_function import PythonFunction


class PythonClass(BaseModel):
    id: str

    name: str

    line_number: int

    base_classes: List[str] = Field(default_factory=list)

    methods: List[PythonFunction] = Field(default_factory=list)