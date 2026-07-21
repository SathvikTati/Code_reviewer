from pydantic import BaseModel


class PythonImport(BaseModel):
    module: str