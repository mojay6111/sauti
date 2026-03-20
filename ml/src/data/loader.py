"""
loader.py — Loads annotated data from CSV/JSON into training-ready format.

Supports:
- CSV exports from Label Studio
- Direct pilot_dataset.csv format
- Multi-label binarization
- Train/val/test splitting with stratification
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)

# All possible labels — must match annotation_schema.json
ALL_LABELS = [
    "hate_speech",
    "offensive_language",
    "distress_trigger",
    "gaslighting",
    "manipulation",
    "ambiguous",
    "clean",
]


class SautiDataset:
    """
    Loads and prepares annotated data for training.

    Usage:
        ds = SautiDataset("data/annotated/pilot_dataset.csv")
        train, val, test = ds.split()
        X_train, y_train = train["text"].tolist(), train["labels_binary"]
    """

    def __init__(self, data_path: str | Path, label_columns: Optional[list[str]] = None):
        self.data_path = Path(data_path)
        self.label_columns = label_columns or ALL_LABELS
        self.mlb = MultiLabelBinarizer(classes=self.label_columns)
        self._df: Optional[pd.DataFrame] = None

    def load(self) -> "SautiDataset":
        suffix = self.data_path.suffix.lower()

        if suffix == ".csv":
            self._df = self._load_csv()
        elif suffix == ".json":
            self._df = self._load_label_studio_json()
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        logger.info(f"Loaded {len(self._df)} examples from {self.data_path}")
        self._validate()
        return self

    def _load_csv(self) -> pd.DataFrame:
        df = pd.read_csv(self.data_path)

        # Normalize category column — may be comma-separated multi-label
        df["labels"] = df["category"].apply(self._parse_labels)
        df["text"] = df["text"].fillna("").astype(str)
        df["language"] = df.get("language", pd.Series(["mixed"] * len(df)))
        df["severity"] = pd.to_numeric(df.get("severity", 1), errors="coerce").fillna(1).astype(int)

        return df[["id", "text", "language", "labels", "severity"]]

    def _load_label_studio_json(self) -> pd.DataFrame:
        """Parse Label Studio export JSON format."""
        with open(self.data_path) as f:
            raw = json.load(f)

        records = []
        for item in raw:
            text = item.get("data", {}).get("text", "")
            annotations = item.get("annotations", [])
            if not annotations:
                continue

            # Take the first completed annotation
            ann = annotations[0]
            results = ann.get("result", [])

            labels = []
            severity = 1
            language = "mixed"

            for r in results:
                if r.get("from_name") == "category":
                    labels.extend(r["value"].get("choices", []))
                elif r.get("from_name") == "severity":
                    severity = r["value"].get("rating", 1)
                elif r.get("from_name") == "language":
                    lang_choices = r["value"].get("choices", ["mixed"])
                    language = lang_choices[0] if lang_choices else "mixed"

            records.append({
                "id": item.get("id", ""),
                "text": text,
                "language": language,
                "labels": labels,
                "severity": severity,
            })

        return pd.DataFrame(records)

    def _parse_labels(self, raw) -> list[str]:
        if isinstance(raw, list):
            return raw
        if isinstance(raw, str):
            # Handle comma-separated labels
            return [l.strip() for l in raw.split(",") if l.strip() in ALL_LABELS]
        return ["clean"]

    def _validate(self):
        assert "text" in self._df.columns, "Missing 'text' column"
        assert "labels" in self._df.columns, "Missing 'labels' column"
        empty = self._df["text"].str.strip().eq("").sum()
        if empty > 0:
            logger.warning(f"{empty} empty text entries found — will be filtered")
        self._df = self._df[self._df["text"].str.strip() != ""]

    def binarize_labels(self) -> np.ndarray:
        """Convert list-of-labels to binary matrix."""
        return self.mlb.fit_transform(self._df["labels"])

    def split(
        self,
        test_size: float = 0.15,
        val_size: float = 0.15,
        random_state: int = 42,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Returns (train_df, val_df, test_df).
        Each df has columns: text, labels, severity, language
        """
        df = self._df.copy()
        df["labels_binary"] = list(self.binarize_labels())

        # First split off test set
        train_val, test = train_test_split(
            df, test_size=test_size, random_state=random_state
        )
        # Then split val from train
        relative_val = val_size / (1 - test_size)
        train, val = train_test_split(
            train_val, test_size=relative_val, random_state=random_state
        )

        logger.info(f"Split: train={len(train)}, val={len(val)}, test={len(test)}")
        return train, val, test

    def label_distribution(self) -> dict:
        """Returns count of each label in the dataset."""
        counts = {label: 0 for label in self.label_columns}
        for labels in self._df["labels"]:
            for label in labels:
                if label in counts:
                    counts[label] += 1
        return counts

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            raise RuntimeError("Call .load() first")
        return self._df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ds = SautiDataset("data/annotated/pilot_dataset.csv").load()
    print("Label distribution:", ds.label_distribution())
    train, val, test = ds.split()
    print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
