"""health.py — GET /health endpoint."""

import time
from fastapi import APIRouter, Request
from api.src.models.schemas import HealthResponse

router = APIRouter()
_start_time = time.time()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(request: Request):
    return HealthResponse(
        status="ok",
        model_loaded=request.app.state.model is not None,
        model_version=request.app.state.model_version,
        uptime_seconds=round(time.time() - _start_time, 1),
    )
