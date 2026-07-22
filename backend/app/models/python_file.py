from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.python_class import PythonClass
from app.models.python_function import PythonFunction
from app.models.python_import import PythonImport


class PythonFile(BaseModel):
    id: str
    
    name: str

    relative_path: str

    absolute_path: str

    size: int

    imports: List[PythonImport] = Field(default_factory=list)

    classes: List[PythonClass] = Field(default_factory=list)

    functions: List[PythonFunction] = Field(default_factory=list)

    # Set when the file could not be parsed (invalid syntax, encoding, etc.);
    # the file is skipped but still recorded.
    parse_error: Optional[str] = None