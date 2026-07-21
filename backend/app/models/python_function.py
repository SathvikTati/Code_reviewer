from typing import List

from pydantic import BaseModel, Field

from app.models.python_parameter import PythonParameter
from app.models.python_call import PythonCall


class PythonFunction(BaseModel):
    id: str

    name: str

    line_number: int

    parameters: List[PythonParameter] = Field(default_factory=list)

    decorators: List[str] = Field(default_factory=list)

    calls: List[PythonCall] = Field(default_factory=list)