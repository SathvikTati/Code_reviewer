from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.review_controller import router as review_router
from app.telemetry import tracing

# Initialize Phoenix tracing before the app starts serving.
tracing.setup_tracing()

app = FastAPI()

# Allow the frontend to call the API even if opened from a different origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    review_router,
    prefix="/review",
    tags=["Review"]
)

# main.py -> app -> backend -> repo root -> frontend/index.html
FRONTEND_INDEX = Path(__file__).resolve().parents[2] / "frontend" / "index.html"


@app.get("/")
def index():
    return FileResponse(FRONTEND_INDEX)
