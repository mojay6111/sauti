"""
schemas.py — Pydantic models for all API request and response bodies.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class Language(str, Enum):
    en = "en"
    sw = "sw"
    sheng = "sheng"
    mixed = "mixed"
    auto = "auto"  # let the system detect


class Label(str, Enum):
    hate_speech = "hate_speech"
    offensive_language = "offensive_language"
    distress_trigger = "distress_trigger"
    gaslighting = "gaslighting"
    manipulation = "manipulation"
    ambiguous = "ambiguous"
    clean = "clean"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Text to analyze. Supports English, Swahili, Sheng, and mixed.",
        examples=["Wewe ni mjinga kabisa na hujui kitu"]
    )
    language: Language = Field(
        default=Language.auto,
        description="Language hint. Use 'auto' to let the system detect."
    )
    explain: bool = Field(
        default=False,
        description="If true, returns rationale spans highlighting why the text was flagged."
    )
    threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for returning a label. Lower = more sensitive."
    )

    @field_validator("text")
    @classmethod
    def strip_text(cls, v):
        return v.strip()


class FeedbackRequest(BaseModel):
    prediction_id: str = Field(..., description="ID from the original /analyze response")
    correct_labels: list[Label] = Field(..., description="What the labels should have been")
    notes: Optional[str] = Field(None, max_length=1000)
    annotator_id: Optional[str] = Field(None, description="Optional — for trusted annotators")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class LabelPrediction(BaseModel):
    label: Label
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: Optional[int] = Field(None, ge=1, le=5)


class RationaleSpan(BaseModel):
    text: str
    start: int
    end: int
    label: Label


class AnalyzeResponse(BaseModel):
    prediction_id: str
    text: str
    language_detected: Language
    predictions: list[LabelPrediction]
    rationale_spans: Optional[list[RationaleSpan]] = None
    model_version: str
    flagged_for_review: bool = Field(
        description="True if any label is 'ambiguous' or confidence is low — routes to human review"
    )
    processing_time_ms: int


class FeedbackResponse(BaseModel):
    status: str = "received"
    prediction_id: str
    message: str = "Thank you. This will be reviewed for model improvement."


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str
    uptime_seconds: float
