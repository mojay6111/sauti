"""
test_api.py — Integration tests for all Sauti API endpoints.

Run with:
    cd sauti
    pytest api/tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(ROOT))

from api.src.main import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """TestClient with a mocked model so tests run without trained weights."""
    app = create_app()

    # Inject mock model and cleaner into app state
    mock_model = MagicMock()
    mock_model.predict_single.return_value = {
        "text": "test",
        "predictions": [
            {"label": "hate_speech", "confidence": 0.87},
            {"label": "offensive_language", "confidence": 0.61},
        ],
        "model": "baseline_tfidf_lr",
    }

    from ml.src.data.cleaner import TextCleaner
    mock_cleaner = TextCleaner()

    with TestClient(app) as c:
        app.state.model = mock_model
        app.state.cleaner = mock_cleaner
        app.state.model_version = "test_model_v1"
        yield c


VALID_KEY = "dev-local-key-do-not-use-in-prod"
HEADERS = {"X-API-Key": VALID_KEY}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_has_required_fields(self, client):
        r = client.get("/health").json()
        assert "status" in r
        assert "model_loaded" in r
        assert "model_version" in r
        assert "uptime_seconds" in r

    def test_health_no_auth_required(self, client):
        """Health endpoint must not require API key — needed for load balancer checks."""
        r = client.get("/health")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# /v1/analyze
# ---------------------------------------------------------------------------

class TestAnalyze:
    def test_basic_swahili_text(self, client):
        r = client.post(
            "/v1/analyze",
            json={"text": "Wote Somali ni terrorists na wezi"},
            headers=HEADERS,
        )
        assert r.status_code == 200
        data = r.json()
        assert "predictions" in data
        assert len(data["predictions"]) > 0
        assert "prediction_id" in data
        assert "language_detected" in data

    def test_predictions_have_required_fields(self, client):
        r = client.post(
            "/v1/analyze",
            json={"text": "Wewe ni mjinga kabisa"},
            headers=HEADERS,
        ).json()
        for p in r["predictions"]:
            assert "label" in p
            assert "confidence" in p
            assert 0.0 <= p["confidence"] <= 1.0

    def test_valid_labels_only(self, client):
        valid_labels = {
            "hate_speech", "offensive_language", "distress_trigger",
            "gaslighting", "manipulation", "ambiguous", "clean"
        }
        r = client.post(
            "/v1/analyze",
            json={"text": "Test text here"},
            headers=HEADERS,
        ).json()
        for p in r["predictions"]:
            assert p["label"] in valid_labels

    def test_requires_api_key(self, client):
        r = client.post("/v1/analyze", json={"text": "hello"})
        assert r.status_code == 401

    def test_rejects_invalid_key(self, client):
        r = client.post(
            "/v1/analyze",
            json={"text": "hello"},
            headers={"X-API-Key": "fake-wrong-key"},
        )
        assert r.status_code == 403

    def test_rejects_empty_text(self, client):
        r = client.post(
            "/v1/analyze",
            json={"text": ""},
            headers=HEADERS,
        )
        assert r.status_code == 422

    def test_rejects_too_short_text(self, client):
        r = client.post(
            "/v1/analyze",
            json={"text": "hi"},
            headers=HEADERS,
        )
        assert r.status_code in (422, 400)

    def test_rejects_too_long_text(self, client):
        r = client.post(
            "/v1/analyze",
            json={"text": "a" * 5001},
            headers=HEADERS,
        )
        assert r.status_code == 422

    def test_flagged_for_review_present(self, client):
        r = client.post(
            "/v1/analyze",
            json={"text": "This might be ambiguous content"},
            headers=HEADERS,
        ).json()
        assert "flagged_for_review" in r
        assert isinstance(r["flagged_for_review"], bool)

    def test_processing_time_present(self, client):
        r = client.post(
            "/v1/analyze",
            json={"text": "Habari za leo"},
            headers=HEADERS,
        ).json()
        assert "processing_time_ms" in r
        assert r["processing_time_ms"] >= 0

    def test_language_hint_accepted(self, client):
        r = client.post(
            "/v1/analyze",
            json={"text": "Habari za leo", "language": "sw"},
            headers=HEADERS,
        )
        assert r.status_code == 200

    def test_threshold_param(self, client):
        r = client.post(
            "/v1/analyze",
            json={"text": "Test text", "threshold": 0.9},
            headers=HEADERS,
        )
        assert r.status_code == 200

    def test_model_version_in_response(self, client):
        r = client.post(
            "/v1/analyze",
            json={"text": "Tutakukumbuka baada ya uchaguzi"},
            headers=HEADERS,
        ).json()
        assert "model_version" in r
        assert r["model_version"] != ""


# ---------------------------------------------------------------------------
# /v1/feedback
# ---------------------------------------------------------------------------

class TestFeedback:
    def test_submit_feedback(self, client, tmp_path, monkeypatch):
        # Redirect feedback file to temp dir
        import api.src.routes.feedback as fb_module
        monkeypatch.setattr(fb_module, "FEEDBACK_FILE", tmp_path / "feedback.jsonl")

        r = client.post(
            "/v1/feedback",
            json={
                "prediction_id": "test-pred-id-123",
                "correct_labels": ["offensive_language"],
                "notes": "This was clearly an insult",
            },
            headers=HEADERS,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "received"
        assert data["prediction_id"] == "test-pred-id-123"

    def test_feedback_written_to_file(self, client, tmp_path, monkeypatch):
        import api.src.routes.feedback as fb_module
        fb_file = tmp_path / "feedback.jsonl"
        monkeypatch.setattr(fb_module, "FEEDBACK_FILE", fb_file)

        client.post(
            "/v1/feedback",
            json={
                "prediction_id": "abc-123",
                "correct_labels": ["clean"],
            },
            headers=HEADERS,
        )

        assert fb_file.exists()
        import json
        lines = fb_file.read_text().strip().split("\n")
        record = json.loads(lines[-1])
        assert record["prediction_id"] == "abc-123"
        assert "clean" in record["correct_labels"]

    def test_feedback_requires_api_key(self, client):
        r = client.post(
            "/v1/feedback",
            json={"prediction_id": "x", "correct_labels": ["clean"]},
        )
        assert r.status_code == 401

    def test_feedback_requires_correct_labels(self, client):
        r = client.post(
            "/v1/feedback",
            json={"prediction_id": "x"},
            headers=HEADERS,
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Cleaner unit tests (bonus)
# ---------------------------------------------------------------------------

class TestCleaner:
    def setup_method(self):
        from ml.src.data.cleaner import TextCleaner
        self.cleaner = TextCleaner()

    def test_removes_urls(self):
        result = self.cleaner.clean("Check this https://example.com out")
        assert "https" not in result["cleaned"]

    def test_removes_mentions(self):
        result = self.cleaner.clean("Hey @johndoe what do you think")
        assert "@johndoe" not in result["cleaned"]

    def test_normalizes_repeated_chars(self):
        result = self.cleaner.clean("saaaana vizuri")
        assert "aaaa" not in result["cleaned"]

    def test_flags_threat_pattern(self):
        result = self.cleaner.clean("Tutakukumbuka baada ya uchaguzi")
        assert "threat_pattern_detected" in result["flags"]

    def test_normalizes_sheng(self):
        result = self.cleaner.clean("Msee poa sana leo")
        assert "sheng_normalized" in result["flags"]

    def test_empty_text(self):
        result = self.cleaner.clean("")
        assert result["too_short"] is True

    def test_clean_text_passes_through(self):
        result = self.cleaner.clean("Habari za leo ni nzuri sana")
        assert result["cleaned"] != ""
        assert result["too_short"] is False
