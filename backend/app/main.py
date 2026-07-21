from fastapi import FastAPI

from app.api.review_controller import router as review_router

app = FastAPI()

app.include_router(
    review_router,
    prefix="/review",
    tags=["Review"]
)