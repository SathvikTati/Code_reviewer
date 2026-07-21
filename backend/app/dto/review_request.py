from pydantic import BaseModel


class FunctionReviewRequest(BaseModel):

    function_name: str
    question: str