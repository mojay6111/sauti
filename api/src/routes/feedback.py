"""
feedback.py — POST /feedback endpoint.

Captures human corrections to model predictions.
These feed back into the annotation pipeline for retraining.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, Request
from loguru import logger

from api.src.models.schemas import FeedbackRequest, FeedbackResponse
from api.src.middleware.auth import verify_api_key

router = APIRouter()

FEEDBACK_DIR = Path("data/feedback")
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
FEEDBACK_FILE = FEEDBACK_DIR / "corrections.jsonl"


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit a label correction",
    tags=["Feedback"],
)
async def submit_feedback(
    request: Request,
    body: FeedbackRequest,
    api_key: str = Depends(verify_api_key),
):
    record = {
        "id": str(uuid.uuid4()),
        "prediction_id": body.prediction_id,
        "correct_labels": [l.value for l in body.correct_labels],
        "notes": body.notes,
        "annotator_id": body.annotator_id,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "api_key_prefix": api_key[:8] + "...",
    }

    with open(FEEDBACK_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

    logger.info(f"Feedback received for prediction {body.prediction_id}")

    return FeedbackResponse(prediction_id=body.prediction_id)
