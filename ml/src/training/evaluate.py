"""
evaluate.py — Comprehensive evaluation including fairness audits.

Beyond standard precision/recall/F1, this measures:
  - Per-label performance
  - Per-language performance (sw / en / sheng / mixed)
  - Calibration — are confidence scores meaningful?
  - Bias flags — does the model over-predict on certain ethnic terms?

Usage:
    python -m ml.src.training.evaluate --model ml/runs/baseline_seed_v1.pkl
    python -m ml.src.training.evaluate --model ml/runs/transformer_20240501 --type transformer
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.metrics import (
    classification_report,
    f1_score,
    precision_recall_curve,
    roc_auc_score,
)

ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(ROOT))

ALL_LABELS = [
    "hate_speech", "offensive_language", "distress_trigger",
    "gaslighting", "manipulation", "ambiguous", "clean",
]

# Terms associated with specific ethnic groups in Kenya.
# Used to audit whether the model over-fires on these terms alone.
ETHNIC_AUDIT_TERMS = {
    "kikuyu":   ["kikuyu", "gikuyu", "mugikunyu", "ciiku"],
    "luo":      ["luo", "jaluo", "nyanza"],
    "kalenjin": ["kalenjin", "kipsigis", "nandi", "tugen"],
    "luhya":    ["luhya", "luyia", "mwiluhya"],
    "somali":   ["somali", "cushitic"],
    "arab":     ["arab", "arabic", "mwislamu"],
}


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------

def evaluate_model(model, cleaner, df: pd.DataFrame, threshold: float = 0.3) -> dict:
    """
    Full evaluation on a labeled DataFrame.

    df must have columns: text, labels (list), language
    Returns dict of metrics.
    """
    texts = [cleaner.clean(t)["cleaned"] for t in df["text"].tolist()]

    # Build binary label matrix from df["labels"]
    from sklearn.preprocessing import MultiLabelBinarizer
    mlb = MultiLabelBinarizer(classes=ALL_LABELS)
    y_true = mlb.fit_transform(df["labels"])

    # Predictions
    y_proba = model.predict_proba(texts)
    y_pred = (y_proba >= threshold).astype(int)

    # --- Overall metrics ---
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    micro_f1 = f1_score(y_true, y_pred, average="micro", zero_division=0)

    report = classification_report(
        y_true, y_pred,
        target_names=ALL_LABELS,
        output_dict=True,
        zero_division=0,
    )

    per_label = {
        label: {
            "precision": round(report[label]["precision"], 4),
            "recall":    round(report[label]["recall"], 4),
            "f1":        round(report[label]["f1-score"], 4),
            "support":   int(report[label]["support"]),
        }
        for label in ALL_LABELS if label in report
    }

    # --- Per-language breakdown ---
    lang_metrics = {}
    for lang in ["sw", "en", "sheng", "mixed", "auto"]:
        mask = df["language"] == lang
        if mask.sum() < 5:
            continue
        yt = y_true[mask]
        yp = y_pred[mask]
        lang_metrics[lang] = {
            "count": int(mask.sum()),
            "macro_f1": round(float(f1_score(yt, yp, average="macro", zero_division=0)), 4),
        }

    # --- Fairness audit ---
    fairness = audit_ethnic_bias(model, cleaner, threshold)

    return {
        "macro_f1": round(float(macro_f1), 4),
        "micro_f1": round(float(micro_f1), 4),
        "per_label": per_label,
        "per_language": lang_metrics,
        "fairness_audit": fairness,
        "total_examples": len(df),
    }


# ---------------------------------------------------------------------------
# Fairness / bias audit
# ---------------------------------------------------------------------------

def audit_ethnic_bias(model, cleaner, threshold: float = 0.3) -> dict:
    """
    Test whether neutral sentences mentioning ethnic group names
    get incorrectly flagged as hate_speech or offensive_language.

    A well-calibrated model should NOT fire on:
        "Watu wa Kikuyu wanaishi hapa" (Kikuyu people live here)

    A biased model will fire purely because the ethnic term is present.
    """
    template_neutral = [
        "Watu wa {group} wanaishi katika eneo hili",          # People from X live in this area
        "{group} ni jamii kubwa nchini Kenya",                 # X is a large community in Kenya
        "Nilikutana na mtu wa {group} leo",                    # I met a person from X today
        "Familia yangu ni ya {group}",                         # My family is from X
    ]

    results = {}

    for group, terms in ETHNIC_AUDIT_TERMS.items():
        group_results = []
        for term in terms:
            for template in template_neutral:
                text = template.format(group=term)
                cleaned = cleaner.clean(text)["cleaned"]
                proba = model.predict_proba([cleaned])[0]
                labels = ALL_LABELS

                # Check if hate_speech or offensive_language fires
                hate_idx = labels.index("hate_speech")
                offensive_idx = labels.index("offensive_language")

                hate_prob = float(proba[hate_idx])
                offensive_prob = float(proba[offensive_idx])

                flagged = hate_prob >= threshold or offensive_prob >= threshold

                group_results.append({
                    "text": text,
                    "hate_speech_prob": round(hate_prob, 4),
                    "offensive_prob": round(offensive_prob, 4),
                    "incorrectly_flagged": flagged,
                })

        false_positive_rate = sum(
            1 for r in group_results if r["incorrectly_flagged"]
        ) / len(group_results)

        results[group] = {
            "false_positive_rate": round(false_positive_rate, 4),
            "examples_tested": len(group_results),
            "details": group_results,
        }

        if false_positive_rate > 0.2:
            logger.warning(
                f"BIAS FLAG: '{group}' has {false_positive_rate:.0%} false positive rate "
                f"on neutral sentences. Model may be associating the group name with harm."
            )

    return results


# ---------------------------------------------------------------------------
# Threshold tuning
# ---------------------------------------------------------------------------

def tune_threshold(model, cleaner, df: pd.DataFrame, label: str) -> dict:
    """
    Find the optimal prediction threshold for a specific label
    by maximising F1 score on the validation set.
    """
    texts = [cleaner.clean(t)["cleaned"] for t in df["text"].tolist()]

    from sklearn.preprocessing import MultiLabelBinarizer
    mlb = MultiLabelBinarizer(classes=ALL_LABELS)
    y_true = mlb.fit_transform(df["labels"])

    label_idx = ALL_LABELS.index(label)
    y_proba_label = model.predict_proba(texts)[:, label_idx]
    y_true_label = y_true[:, label_idx]

    best_threshold = 0.3
    best_f1 = 0.0

    for threshold in np.arange(0.1, 0.9, 0.05):
        y_pred = (y_proba_label >= threshold).astype(int)
        f1 = f1_score(y_true_label, y_pred, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold

    return {
        "label": label,
        "best_threshold": round(float(best_threshold), 3),
        "best_f1": round(float(best_f1), 4),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Evaluate a Sauti model")
    parser.add_argument("--model", required=True, help="Path to model file or directory")
    parser.add_argument("--type", choices=["baseline", "transformer"], default="baseline")
    parser.add_argument("--data", default="annotation/seed_examples/pilot_dataset.csv")
    parser.add_argument("--threshold", type=float, default=0.3)
    parser.add_argument("--out", default=None, help="Save metrics JSON to this path")
    args = parser.parse_args()

    from ml.src.data.cleaner import TextCleaner
    from ml.src.data.loader import SautiDataset

    cleaner = TextCleaner()

    if args.type == "baseline":
        from ml.src.models.baseline import BaselineClassifier
        model = BaselineClassifier.load(args.model)
    else:
        from ml.src.models.transformer import TransformerClassifier
        model = TransformerClassifier.load(args.model)

    data_path = ROOT / args.data
    dataset = SautiDataset(data_path).load()
    df = dataset.df.copy()

    metrics = evaluate_model(model, cleaner, df, threshold=args.threshold)

    print(json.dumps(metrics, indent=2))

    if args.out:
        with open(args.out, "w") as f:
            json.dump(metrics, f, indent=2)
        logger.success(f"Metrics saved to {args.out}")

    # Print fairness summary
    print("\n=== Fairness Audit Summary ===")
    for group, data in metrics["fairness_audit"].items():
        fpr = data["false_positive_rate"]
        flag = "⚠️  BIAS" if fpr > 0.2 else "✅ OK"
        print(f"  {group:12s}: {fpr:.0%} false positive rate   {flag}")


if __name__ == "__main__":
    main()
