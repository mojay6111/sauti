"""
baseline.py — TF-IDF + Logistic Regression multi-label classifier.

This is Sprint 1's model. It is intentionally simple — its purpose is to:
1. Validate the data pipeline end-to-end
2. Establish a performance floor for transformer models to beat
3. Be fast to train, so we can iterate on data quality quickly

Do not optimize this model. When it plateaus, move to transformer.py.
"""

import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.pipeline import Pipeline
from loguru import logger
from typing import Optional
import json


ALL_LABELS = [
    "hate_speech",
    "offensive_language",
    "distress_trigger",
    "gaslighting",
    "manipulation",
    "ambiguous",
    "clean",
]


class BaselineClassifier:
    """
    TF-IDF + Logistic Regression multi-label classifier.

    Handles Swahili, English, and mixed-language text without
    requiring a multilingual tokenizer — useful for rapid prototyping.
    """

    def __init__(self, labels: list[str] = ALL_LABELS):
        self.labels = labels
        self.pipeline: Optional[Pipeline] = None
        self._is_trained = False

    def build(self) -> "BaselineClassifier":
        """Construct the sklearn pipeline."""
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                analyzer="char_wb",      # character n-grams — better for Sheng/code-switch
                ngram_range=(2, 5),
                max_features=50_000,
                sublinear_tf=True,
                min_df=2,
            )),
            ("clf", OneVsRestClassifier(
                LogisticRegression(
                    C=1.0,
                    max_iter=1000,
                    class_weight="balanced",  # important — harmful content is minority class
                    solver="lbfgs",
                )
            ))
        ])
        return self

    def train(self, texts: list[str], labels_binary: np.ndarray) -> "BaselineClassifier":
        """
        Train the model.

        Args:
            texts: list of raw (cleaned) text strings
            labels_binary: (n_samples, n_labels) binary matrix from MultiLabelBinarizer
        """
        if self.pipeline is None:
            self.build()

        logger.info(f"Training baseline on {len(texts)} examples...")
        self.pipeline.fit(texts, labels_binary)
        self._is_trained = True
        logger.info("Training complete.")
        return self

    def predict(self, texts: list[str]) -> np.ndarray:
        """Returns binary prediction matrix (n_samples, n_labels)."""
        self._check_trained()
        return self.pipeline.predict(texts)

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        """Returns probability matrix (n_samples, n_labels)."""
        self._check_trained()
        return self.pipeline.predict_proba(texts)

    def predict_single(self, text: str, threshold: float = 0.3) -> dict:
        """
        Predict labels for a single text string.

        Returns human-readable result dict suitable for the API response.
        """
        self._check_trained()
        proba = self.pipeline.predict_proba([text])[0]

        results = []
        for label, prob in zip(self.labels, proba):
            if prob >= threshold:
                results.append({
                    "label": label,
                    "confidence": round(float(prob), 4),
                })

        # Sort by confidence descending
        results.sort(key=lambda x: x["confidence"], reverse=True)

        # If nothing exceeds threshold, return clean with low confidence
        if not results:
            results = [{"label": "clean", "confidence": round(float(1 - max(proba)), 4)}]

        return {
            "text": text,
            "predictions": results,
            "model": "baseline_tfidf_lr",
        }

    def evaluate(self, texts: list[str], labels_binary: np.ndarray) -> dict:
        """Evaluate on a test set and return metrics."""
        self._check_trained()
        y_pred = self.predict(texts)

        report = classification_report(
            labels_binary,
            y_pred,
            target_names=self.labels,
            output_dict=True,
            zero_division=0,
        )

        macro_f1 = f1_score(labels_binary, y_pred, average="macro", zero_division=0)
        micro_f1 = f1_score(labels_binary, y_pred, average="micro", zero_division=0)

        logger.info(f"Macro F1: {macro_f1:.4f} | Micro F1: {micro_f1:.4f}")

        return {
            "macro_f1": round(macro_f1, 4),
            "micro_f1": round(micro_f1, 4),
            "per_label": {
                label: {
                    "precision": round(report[label]["precision"], 4),
                    "recall": round(report[label]["recall"], 4),
                    "f1": round(report[label]["f1-score"], 4),
                    "support": int(report[label]["support"]),
                }
                for label in self.labels if label in report
            }
        }

    def save(self, path: str | Path):
        """Pickle the trained pipeline."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        logger.info(f"Model saved to {path}")

    @classmethod
    def load(cls, path: str | Path) -> "BaselineClassifier":
        """Load a pickled model."""
        with open(path, "rb") as f:
            model = pickle.load(f)
        logger.info(f"Model loaded from {path}")
        return model

    def _check_trained(self):
        if not self._is_trained:
            raise RuntimeError("Model not trained. Call .train() first.")


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parents[2]))

    from src.data.cleaner import TextCleaner

    cleaner = TextCleaner()

    # Minimal toy data for smoke test
    texts = [
        "Wote Somali ni terrorists na wezi",
        "Wewe ni mjinga kabisa",
        "Tutakukumbuka baada ya uchaguzi",
        "Hukusema hivyo. Unakumbuka vibaya kila wakati.",
        "Baada ya kila kitu nilichofanya kwako unafanya hivi?",
        "Habari za asubuhi. Leo ni siku nzuri.",
        "Naenda dukani kununua chakula",
        "You're just being too sensitive as always",
        "Malaya wewe unafikiri unajua nini",
        "ODM hawafanyi kazi vizuri hata kidogo",
    ]

    # Fake binary labels for smoke test
    import numpy as np
    labels = np.array([
        [1, 0, 0, 0, 0, 0, 0],  # hate_speech
        [0, 1, 0, 0, 0, 0, 0],  # offensive_language
        [0, 0, 1, 0, 0, 0, 0],  # distress_trigger
        [0, 0, 0, 1, 0, 0, 0],  # gaslighting
        [0, 0, 0, 0, 1, 0, 0],  # manipulation
        [0, 0, 0, 0, 0, 0, 1],  # clean
        [0, 0, 0, 0, 0, 0, 1],  # clean
        [0, 0, 0, 1, 0, 0, 0],  # gaslighting
        [0, 1, 0, 0, 0, 0, 0],  # offensive_language
        [0, 0, 0, 0, 0, 0, 1],  # clean
    ])

    cleaned = [cleaner.clean(t)["cleaned"] for t in texts]

    model = BaselineClassifier().build().train(cleaned, labels)
    result = model.predict_single("Wewe ni umbwa na mjinga")
    print("Prediction:", json.dumps(result, indent=2))
