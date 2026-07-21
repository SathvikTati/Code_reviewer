from pydantic import BaseModel


class RepositoryAnalysisRequest(BaseModel):

    github_url: str