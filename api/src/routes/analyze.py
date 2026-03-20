"""
analyze.py — POST /analyze endpoint.

The main prediction route. Accepts text, runs it through the loaded model,
returns labels with confidence scores and optional rationale spans.
"""

import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger

from api.src.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    LabelPrediction,
    Language,
)
from api.src.middleware.auth import verify_api_key

router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze text for harmful speech",
    description="""
Analyzes text for harmful, distressing, or manipulative content.

Supports **English**, **Swahili**, **Sheng**, and code-switched text.

Returns:
- Detected labels (e.g. `hate_speech`, `gaslighting`)
- Confidence scores per label
- Severity (1–5) per label
- Optional rationale spans highlighting the harmful phrases
- A `flagged_for_review` flag for ambiguous cases
    """,
    tags=["Analysis"],
)
async def analyze_text(
    request: Request,
    body: AnalyzeRequest,
    _: str = Depends(verify_api_key),
):
    start = time.perf_counter()

    model = request.app.state.model
    cleaner = request.app.state.cleaner

    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Try again shortly.")

    # Clean input
    cleaned = cleaner.clean(body.text)
    if cleaned["too_short"]:
        raise HTTPException(status_code=422, detail="Text too short to analyze.")

    # Run prediction
    try:
        raw_result = model.predict_single(
            cleaned["cleaned"],
            threshold=body.threshold,
        )
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed.")

    # Build response predictions
    predictions = [
        LabelPrediction(
            label=p["label"],
            confidence=p["confidence"],
            severity=_estimate_severity(p["label"], p["confidence"]),
        )
        for p in raw_result["predictions"]
    ]

    # Determine if this needs human review
    labels_present = {p.label for p in predictions}
    low_confidence = any(p.confidence < 0.5 for p in predictions if p.label != "clean")
    flagged = "ambiguous" in labels_present or low_confidence

    prediction_id = str(uuid.uuid4())
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    logger.info(
        f"[{prediction_id}] labels={[p.label for p in predictions]} "
        f"flagged={flagged} lang={body.language} ms={elapsed_ms}"
    )

    return AnalyzeResponse(
        prediction_id=prediction_id,
        text=body.text,
        language_detected=_detect_language(body.language, cleaned["cleaned"]),
        predictions=predictions,
        rationale_spans=None,   # populated in Sprint 2 with SHAP
        model_version=request.app.state.model_version,
        flagged_for_review=flagged,
        processing_time_ms=elapsed_ms,
    )


def _estimate_severity(label: str, confidence: float) -> int:
    """
    Rough severity estimate from confidence when no severity model is trained.
    Replace with trained severity head in Sprint 2.
    """
    if confidence >= 0.85:
        return 4
    elif confidence >= 0.65:
        return 3
    elif confidence >= 0.45:
        return 2
    return 1


def _detect_language(hint: Language, text: str) -> Language:
    """
    Language detection. Currently returns the hint if not 'auto'.
    Swap in langdetect or a proper multilingual detector in Sprint 2.
    """
    if hint != Language.auto:
        return hint

    # Very basic heuristic — replace with proper detector
    swahili_markers = ["wewe", "ni", "na", "ya", "wa", "kwa", "hii", "sana", "kabisa"]
    lower = text.lower()
    sw_count = sum(1 for w in swahili_markers if w in lower.split())

    if sw_count >= 3:
        return Language.sw
    elif sw_count >= 1:
        return Language.mixed
    return Language.en
