from fastapi import APIRouter

from app.dto.repository_analysis_request import RepositoryAnalysisRequest
from app.services.review.review_service import ReviewService

router = APIRouter()

review_service = ReviewService()


@router.post("/analyze")
def analyze(request: RepositoryAnalysisRequest):

    response = review_service.analyze_repository(
        request.github_url
    )

    return {
        "analysis": response
    }