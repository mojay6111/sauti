"""
shap_explainer.py — Generates rationale spans for model predictions.

Uses SHAP to identify which words/phrases drove a prediction.
These spans are returned in the API response when explain=True.

Sprint 1: character n-gram importance via SHAP on baseline model.
Sprint 2: attention-based rationale from transformer model.
"""

import numpy as np
from typing import Optional
from loguru import logger


class SautiExplainer:
    """
    Wraps SHAP to generate word-level importance scores
    for a trained BaselineClassifier.

    Usage:
        explainer = SautiExplainer(model)
        spans = explainer.explain("Wewe ni mjinga kabisa", label="offensive_language")
    """

    def __init__(self, model, labels: list[str]):
        self.model = model
        self.labels = labels
        self._shap_explainer = None
        self._initialized = False

    def _lazy_init(self, background_texts: list[str]):
        """
        Initialize SHAP explainer lazily on first use.
        Requires a small background corpus.
        """
        try:
            import shap

            def predict_fn(texts):
                """Wrapper that returns probability array for SHAP."""
                return self.model.predict_proba(list(texts))

            self._shap_explainer = shap.Explainer(
                predict_fn,
                masker=shap.maskers.Text(r"\W+"),  # word-level masking
                output_names=self.labels,
            )
            self._initialized = True
            logger.info("SHAP explainer initialized.")
        except ImportError:
            logger.warning("SHAP not installed. Explainability disabled.")
        except Exception as e:
            logger.warning(f"SHAP init failed: {e}")

    def explain(
        self,
        text: str,
        label: Optional[str] = None,
        top_n: int = 5,
        background_texts: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Generate rationale spans for a text.

        Args:
            text: The text to explain
            label: Which label to explain (if None, explains the top predicted label)
            top_n: How many spans to return
            background_texts: Small background corpus for SHAP initialization

        Returns:
            List of {text, start, end, label, importance} dicts
        """
        if not self._initialized:
            bg = background_texts or [text]  # minimal fallback
            self._lazy_init(bg)

        if not self._initialized:
            return self._fallback_spans(text, label, top_n)

        try:
            import shap
            shap_values = self._shap_explainer([text])

            # Determine label index
            label_idx = 0
            if label and label in self.labels:
                label_idx = self.labels.index(label)

            # Extract token importances
            tokens = shap_values.data[0]
            importances = shap_values.values[0][:, label_idx]

            # Build spans with positions
            spans = []
            cursor = 0
            for token, importance in zip(tokens, importances):
                start = text.find(token, cursor)
                if start == -1:
                    continue
                end = start + len(token)
                cursor = end
                if abs(importance) > 0.01:  # filter noise
                    spans.append({
                        "text": token,
                        "start": start,
                        "end": end,
                        "label": label or self.labels[label_idx],
                        "importance": round(float(importance), 4),
                    })

            # Return top N by absolute importance
            spans.sort(key=lambda x: abs(x["importance"]), reverse=True)
            return spans[:top_n]

        except Exception as e:
            logger.warning(f"SHAP explanation failed: {e}")
            return self._fallback_spans(text, label, top_n)

    def _fallback_spans(self, text: str, label: Optional[str], top_n: int) -> list[dict]:
        """
        Simple heuristic fallback when SHAP is unavailable.
        Returns the words most likely to be harmful based on a basic lexicon.
        Remove this once SHAP is working — it is not a substitute.
        """
        from ml.src.data.cleaner import THREAT_PATTERNS
        import re

        spans = []
        words = text.split()
        cursor = 0

        for word in words:
            start = text.find(word, cursor)
            end = start + len(word)
            cursor = end

            # Flag if word appears in threat patterns
            is_flagged = any(
                re.search(p, word, re.IGNORECASE)
                for p in THREAT_PATTERNS
            )
            if is_flagged:
                spans.append({
                    "text": word,
                    "start": start,
                    "end": end,
                    "label": label or "unknown",
                    "importance": 0.5,  # placeholder — not a real score
                })

        return spans[:top_n]


if __name__ == "__main__":
    # Smoke test
    from ml.src.models.baseline import BaselineClassifier
    from ml.src.data.cleaner import TextCleaner
    from ml.src.data.loader import ALL_LABELS
    import numpy as np

    cleaner = TextCleaner()

    texts = ["Wewe ni mjinga kabisa", "Tutakukumbuka baada ya uchaguzi"]
    labels_binary = np.array([
        [0, 1, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0],
    ])

    cleaned = [cleaner.clean(t)["cleaned"] for t in texts]
    model = BaselineClassifier(labels=ALL_LABELS).build().train(cleaned, labels_binary)

    explainer = SautiExplainer(model, labels=ALL_LABELS)
    spans = explainer.explain(
        "Wewe ni mjinga kabisa",
        label="offensive_language",
        background_texts=cleaned,
    )
    print("Rationale spans:", spans)
