"""
train.py — Main training entrypoint for Sauti.

Usage:
    python -m src.training.train                         # uses config.yaml defaults
    python -m src.training.train --model baseline
    python -m src.training.train --model transformer --backbone Davlan/afro-xlmr-large
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

import yaml
from loguru import logger

# Add project root to path
ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(ROOT))

from ml.src.data.cleaner import TextCleaner
from ml.src.data.loader import SautiDataset
from ml.src.models.baseline import BaselineClassifier


def load_config(config_path: str = None) -> dict:
    default_path = Path(__file__).parent / "config.yaml"
    path = Path(config_path) if config_path else default_path
    with open(path) as f:
        return yaml.safe_load(f)


def train_baseline(config: dict, train_df, val_df, test_df):
    logger.info("Training baseline (TF-IDF + LR)...")

    cleaner = TextCleaner()
    bc = config["baseline"]

    def clean_texts(df):
        return [cleaner.clean(t)["cleaned"] for t in df["text"].tolist()]

    X_train = clean_texts(train_df)
    X_val   = clean_texts(val_df)
    X_test  = clean_texts(test_df)

    import numpy as np
    y_train = np.vstack(train_df["labels_binary"].tolist())
    y_val   = np.vstack(val_df["labels_binary"].tolist())
    y_test  = np.vstack(test_df["labels_binary"].tolist())

    model = BaselineClassifier(labels=config["model"]["labels"])
    model.build()
    model.train(X_train, y_train)

    # Evaluate on val
    val_metrics = model.evaluate(X_val, y_val)
    logger.info(f"Val metrics: {json.dumps(val_metrics, indent=2)}")

    # Evaluate on test
    test_metrics = model.evaluate(X_test, y_test)
    logger.info(f"Test metrics: {json.dumps(test_metrics, indent=2)}")

    # Save model
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = ROOT / "ml" / "runs" / f"baseline_{run_id}.pkl"
    model.save(save_path)

    # Save metrics
    metrics_path = ROOT / "ml" / "runs" / f"baseline_{run_id}_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump({"val": val_metrics, "test": test_metrics}, f, indent=2)

    return model, test_metrics


def main():
    parser = argparse.ArgumentParser(description="Train Sauti harmful speech classifier")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--model", choices=["baseline", "transformer"], default=None)
    parser.add_argument("--backbone", default=None, help="HuggingFace model name (transformer only)")
    parser.add_argument("--data", default=None, help="Path to annotated data CSV/JSON")
    args = parser.parse_args()

    config = load_config(args.config)

    # CLI overrides
    if args.model:
        config["model"]["type"] = args.model
    if args.backbone:
        config["model"]["backbone"] = args.backbone
    if args.data:
        config["data"]["train_path"] = args.data

    # Load dataset
    data_path = ROOT / config["data"]["train_path"]
    logger.info(f"Loading data from {data_path}")

    dataset = SautiDataset(data_path).load()
    dist = dataset.label_distribution()
    logger.info(f"Label distribution: {dist}")

    train_df, val_df, test_df = dataset.split(
        test_size=config["data"]["test_size"],
        val_size=config["data"]["val_size"],
        random_state=config["data"]["random_state"],
    )

    model_type = config["model"]["type"]

    if model_type == "baseline":
        model, metrics = train_baseline(config, train_df, val_df, test_df)
        logger.success(f"Done. Macro F1: {metrics['macro_f1']}")

    elif model_type == "transformer":
        from ml.src.models.transformer import TransformerClassifier
        from ml.src.data.cleaner import TextCleaner

        backbone = config["model"].get("backbone") or "bert-base-multilingual-cased"
        tc = config["transformer"]
        cleaner = TextCleaner()

        def clean_texts(df):
            return [cleaner.clean(t)["cleaned"] for t in df["text"].tolist()]

        import numpy as np
        X_train = clean_texts(train_df)
        X_val   = clean_texts(val_df)
        X_test  = clean_texts(test_df)
        y_train = np.vstack(train_df["labels_binary"].tolist())
        y_val   = np.vstack(val_df["labels_binary"].tolist())
        y_test  = np.vstack(test_df["labels_binary"].tolist())

        model = TransformerClassifier(backbone=backbone, labels=config["model"]["labels"])
        best_metrics = model.train(
            X_train, y_train, X_val, y_val,
            batch_size=tc["batch_size"],
            num_epochs=tc["num_epochs"],
            learning_rate=tc["learning_rate"],
            warmup_steps=tc["warmup_steps"],
            prediction_threshold=tc["prediction_threshold"],
        )

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = ROOT / "ml" / "runs" / f"transformer_{run_id}"
        model.save(save_dir)

        metrics_path = save_dir / "metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(best_metrics, f, indent=2)

        logger.success(f"Transformer done. Best val macro F1: {best_metrics.get('macro_f1')}")

    else:
        logger.error(f"Unknown model type: {model_type}")
        sys.exit(1)


if __name__ == "__main__":
    main()
