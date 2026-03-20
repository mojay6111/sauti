"""
transformer.py — AfroXLM-R (or mBERT) fine-tuned multi-label classifier.

This is Sprint 2's model. Replaces the TF-IDF baseline once you have
200+ annotated examples. Handles Swahili, Sheng, and code-switching
significantly better than character n-grams.

Recommended backbone: "Davlan/afro-xlmr-large"
  - Pre-trained on 17 African languages including Swahili
  - Handles code-switching between African languages and English
  - 560M params — requires GPU for training, CPU for inference is slow

Fallback backbone: "bert-base-multilingual-cased"
  - Pre-trained on 104 languages including Swahili
  - 110M params — CPU-viable for inference
  - Less accurate on Sheng / code-switching

Usage:
    model = TransformerClassifier(backbone="Davlan/afro-xlmr-large")
    model.train(train_texts, train_labels, val_texts, val_labels)
    result = model.predict_single("Wewe ni mjinga kabisa")
"""

import json
import os
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from loguru import logger
from torch import nn
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModel,
    get_linear_schedule_with_warmup,
)

ALL_LABELS = [
    "hate_speech",
    "offensive_language",
    "distress_trigger",
    "gaslighting",
    "manipulation",
    "ambiguous",
    "clean",
]

RECOMMENDED_BACKBONE = "Davlan/afro-xlmr-large"
FALLBACK_BACKBONE = "bert-base-multilingual-cased"


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class SautiTextDataset(Dataset):
    def __init__(self, texts: list[str], labels: np.ndarray, tokenizer, max_length: int = 256):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokenizer(
            self.texts[idx],
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": torch.tensor(self.labels[idx], dtype=torch.float),
        }


# ---------------------------------------------------------------------------
# Model architecture
# ---------------------------------------------------------------------------

class SautiTransformerHead(nn.Module):
    """
    Transformer encoder + multi-label classification head.
    Uses [CLS] token representation → dropout → linear → sigmoid.
    """

    def __init__(self, backbone_name: str, num_labels: int, dropout: float = 0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(backbone_name)
        hidden_size = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, num_labels)

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls = outputs.last_hidden_state[:, 0, :]   # [CLS] token
        cls = self.dropout(cls)
        logits = self.classifier(cls)
        return logits                               # raw logits — sigmoid applied at loss/predict


# ---------------------------------------------------------------------------
# Classifier wrapper
# ---------------------------------------------------------------------------

class TransformerClassifier:
    def __init__(
        self,
        backbone: str = RECOMMENDED_BACKBONE,
        labels: list[str] = ALL_LABELS,
        max_length: int = 256,
        device: Optional[str] = None,
    ):
        self.backbone = backbone
        self.labels = labels
        self.max_length = max_length
        self.num_labels = len(labels)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self._is_trained = False

        logger.info(f"TransformerClassifier: backbone={backbone} device={self.device}")
        if self.device == "cpu":
            logger.warning(
                "Running on CPU. Training will be slow. "
                "Use a GPU instance or Google Colab for AfroXLM-R training."
            )

    def _load_tokenizer(self):
        if self.tokenizer is None:
            logger.info(f"Loading tokenizer: {self.backbone}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.backbone)

    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading model: {self.backbone}")
            self.model = SautiTransformerHead(self.backbone, self.num_labels)
            self.model.to(self.device)

    def train(
        self,
        train_texts: list[str],
        train_labels: np.ndarray,
        val_texts: list[str],
        val_labels: np.ndarray,
        batch_size: int = 16,
        num_epochs: int = 5,
        learning_rate: float = 2e-5,
        warmup_steps: int = 100,
        weight_decay: float = 0.01,
        prediction_threshold: float = 0.4,
    ) -> dict:
        """
        Fine-tune on annotated data.

        Returns dict of best val metrics.
        """
        self._load_tokenizer()
        self._load_model()
        self.prediction_threshold = prediction_threshold

        train_ds = SautiTextDataset(train_texts, train_labels, self.tokenizer, self.max_length)
        val_ds = SautiTextDataset(val_texts, val_labels, self.tokenizer, self.max_length)

        train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
        val_dl = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

        # Optimizer — weight decay on all params except bias and LayerNorm
        no_decay = ["bias", "LayerNorm.weight"]
        optimizer_groups = [
            {
                "params": [
                    p for n, p in self.model.named_parameters()
                    if not any(nd in n for nd in no_decay)
                ],
                "weight_decay": weight_decay,
            },
            {
                "params": [
                    p for n, p in self.model.named_parameters()
                    if any(nd in n for nd in no_decay)
                ],
                "weight_decay": 0.0,
            },
        ]
        optimizer = torch.optim.AdamW(optimizer_groups, lr=learning_rate)

        total_steps = len(train_dl) * num_epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps,
        )

        loss_fn = nn.BCEWithLogitsLoss(
            # Upweight rare harmful classes — clean is majority
            pos_weight=torch.ones(self.num_labels).to(self.device) * 3.0
        )

        best_val_f1 = 0.0
        best_metrics = {}

        for epoch in range(num_epochs):
            # --- Train ---
            self.model.train()
            total_loss = 0.0

            for batch in train_dl:
                optimizer.zero_grad()
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                targets = batch["labels"].to(self.device)

                logits = self.model(input_ids, attention_mask)
                loss = loss_fn(logits, targets)
                loss.backward()

                nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                total_loss += loss.item()

            avg_loss = total_loss / len(train_dl)

            # --- Validate ---
            metrics = self._evaluate_loader(val_dl, loss_fn)
            logger.info(
                f"Epoch {epoch+1}/{num_epochs} | "
                f"loss={avg_loss:.4f} | "
                f"val_loss={metrics['loss']:.4f} | "
                f"val_f1={metrics['macro_f1']:.4f}"
            )

            if metrics["macro_f1"] > best_val_f1:
                best_val_f1 = metrics["macro_f1"]
                best_metrics = metrics
                self._best_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}

        # Restore best weights
        if hasattr(self, "_best_state"):
            self.model.load_state_dict(
                {k: v.to(self.device) for k, v in self._best_state.items()}
            )

        self._is_trained = True
        logger.success(f"Training complete. Best val macro F1: {best_val_f1:.4f}")
        return best_metrics

    def _evaluate_loader(self, loader, loss_fn) -> dict:
        from sklearn.metrics import f1_score

        self.model.eval()
        total_loss = 0.0
        all_preds = []
        all_targets = []

        with torch.no_grad():
            for batch in loader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                targets = batch["labels"].to(self.device)

                logits = self.model(input_ids, attention_mask)
                loss = loss_fn(logits, targets)
                total_loss += loss.item()

                probs = torch.sigmoid(logits).cpu().numpy()
                preds = (probs >= getattr(self, "prediction_threshold", 0.4)).astype(int)
                all_preds.append(preds)
                all_targets.append(targets.cpu().numpy())

        y_pred = np.vstack(all_preds)
        y_true = np.vstack(all_targets)

        macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
        micro_f1 = f1_score(y_true, y_pred, average="micro", zero_division=0)

        return {
            "loss": total_loss / len(loader),
            "macro_f1": round(float(macro_f1), 4),
            "micro_f1": round(float(micro_f1), 4),
        }

    def predict_single(self, text: str, threshold: Optional[float] = None) -> dict:
        """Predict labels for a single text string."""
        self._check_ready()
        thresh = threshold or getattr(self, "prediction_threshold", 0.4)

        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        self.model.eval()
        with torch.no_grad():
            logits = self.model(
                encoding["input_ids"].to(self.device),
                encoding["attention_mask"].to(self.device),
            )
            probs = torch.sigmoid(logits).cpu().numpy()[0]

        results = [
            {"label": label, "confidence": round(float(prob), 4)}
            for label, prob in zip(self.labels, probs)
            if prob >= thresh
        ]
        results.sort(key=lambda x: x["confidence"], reverse=True)

        if not results:
            results = [{"label": "clean", "confidence": round(float(1 - max(probs)), 4)}]

        return {
            "text": text,
            "predictions": results,
            "model": f"transformer_{Path(self.backbone).name}",
        }

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        """Returns (n_samples, n_labels) probability array."""
        self._check_ready()
        all_probs = []

        for text in texts:
            enc = self.tokenizer(
                text, max_length=self.max_length,
                padding="max_length", truncation=True, return_tensors="pt"
            )
            self.model.eval()
            with torch.no_grad():
                logits = self.model(
                    enc["input_ids"].to(self.device),
                    enc["attention_mask"].to(self.device),
                )
                probs = torch.sigmoid(logits).cpu().numpy()[0]
            all_probs.append(probs)

        return np.array(all_probs)

    def save(self, directory: str | Path):
        """Save model, tokenizer, and config to a directory."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        self.model.encoder.save_pretrained(directory / "encoder")
        self.tokenizer.save_pretrained(directory / "tokenizer")
        torch.save(self.model.classifier.state_dict(), directory / "classifier_head.pt")

        config = {
            "backbone": self.backbone,
            "labels": self.labels,
            "max_length": self.max_length,
            "prediction_threshold": getattr(self, "prediction_threshold", 0.4),
        }
        with open(directory / "config.json", "w") as f:
            json.dump(config, f, indent=2)

        logger.success(f"Transformer model saved to {directory}")

    @classmethod
    def load(cls, directory: str | Path) -> "TransformerClassifier":
        """Load a saved transformer model."""
        directory = Path(directory)
        with open(directory / "config.json") as f:
            config = json.load(f)

        instance = cls(
            backbone=config["backbone"],
            labels=config["labels"],
            max_length=config["max_length"],
        )
        instance.prediction_threshold = config["prediction_threshold"]
        instance._load_tokenizer()

        # Override tokenizer with saved version
        instance.tokenizer = AutoTokenizer.from_pretrained(directory / "tokenizer")

        instance.model = SautiTransformerHead(
            directory / "encoder",   # load from local path
            len(config["labels"])
        )
        instance.model.classifier.load_state_dict(
            torch.load(directory / "classifier_head.pt", map_location=instance.device)
        )
        instance.model.to(instance.device)
        instance._is_trained = True

        logger.success(f"Transformer model loaded from {directory}")
        return instance

    def _check_ready(self):
        if not self._is_trained or self.model is None:
            raise RuntimeError(
                "Model not trained. Call .train() or .load() first."
            )
