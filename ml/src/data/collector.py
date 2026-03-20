"""
collector.py — Data ingestion for Sauti.

Sources supported:
  1. CSV upload  — any CSV with a 'text' column
  2. Twitter/X   — bearer token search (recent 7 days, Academic for more)
  3. Plain text  — paste a list of strings directly

All collected data lands in data/raw/ with a provenance manifest.
It is NEVER written directly to data/annotated/ — raw and annotated are
strictly separate to preserve data lineage.

Usage:
    from ml.src.data.collector import collect_csv, collect_twitter

    collect_csv("my_posts.csv", source_tag="facebook_export")
    collect_twitter(query="(ukabila OR kikabila) lang:sw", max_results=100)
"""

import csv
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Provenance manifest
# ---------------------------------------------------------------------------

def _write_manifest(batch_id: str, source: str, count: int, meta: dict):
    manifest = {
        "batch_id": batch_id,
        "source": source,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "record_count": count,
        "meta": meta,
        "privacy_note": (
            "Raw data — not yet anonymized. "
            "Do not share outside annotation team. "
            "Delete PII before annotating."
        ),
    }
    path = RAW_DIR / f"{batch_id}_manifest.json"
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest written: {path}")


# ---------------------------------------------------------------------------
# 1. CSV ingestion
# ---------------------------------------------------------------------------

def collect_csv(
    filepath: str | Path,
    text_column: str = "text",
    source_tag: str = "csv_upload",
    language_column: Optional[str] = None,
    deduplicate: bool = True,
) -> Path:
    """
    Ingest a CSV file into data/raw/.

    Args:
        filepath:        Path to input CSV
        text_column:     Name of the column containing text
        source_tag:      Label for provenance (e.g. 'twitter', 'facebook_group')
        language_column: Optional column with language hints ('en'/'sw'/'sheng')
        deduplicate:     Remove exact duplicate texts

    Returns:
        Path to the written JSONL file in data/raw/
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"CSV not found: {filepath}")

    records = []
    seen_texts: set[str] = set()

    with open(filepath, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)

        if text_column not in (reader.fieldnames or []):
            raise ValueError(
                f"Column '{text_column}' not found. Available: {reader.fieldnames}"
            )

        for row in reader:
            text = row.get(text_column, "").strip()
            if not text:
                continue
            if deduplicate:
                if text in seen_texts:
                    continue
                seen_texts.add(text)

            records.append({
                "id": str(uuid.uuid4()),
                "text": text,
                "language": row.get(language_column, "auto") if language_column else "auto",
                "source": source_tag,
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "raw_row": {k: v for k, v in row.items() if k != text_column},
            })

    if not records:
        logger.warning(f"No usable records found in {filepath}")
        return None

    batch_id = f"{source_tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_path = RAW_DIR / f"{batch_id}.jsonl"

    with open(out_path, "w") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    _write_manifest(batch_id, source_tag, len(records), {"source_file": str(filepath)})
    logger.success(f"Collected {len(records)} records → {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# 2. Twitter/X ingestion
# ---------------------------------------------------------------------------

def collect_twitter(
    query: str,
    max_results: int = 100,
    bearer_token: Optional[str] = None,
    source_tag: str = "twitter",
) -> Optional[Path]:
    """
    Collect tweets matching a query using the Twitter v2 API.

    Requires TWITTER_BEARER_TOKEN in env or passed directly.

    Good Kenyan queries:
        - "ukabila OR kikabila lang:sw"         # tribalism discourse
        - "chuki OR ubaguzi lang:sw"            # hate/discrimination
        - "(wewe ni mjinga OR umbwa) lang:sw"   # offensive language
        - "kutoka Kenya -is:retweet lang:sw"    # general Swahili KE

    Note: Free tier gives 7 days history, 500k tweets/month.
    Academic Research gives full archive — apply at developer.twitter.com.
    """
    token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
    if not token:
        logger.error(
            "No Twitter bearer token. Set TWITTER_BEARER_TOKEN in .env "
            "or pass bearer_token= argument."
        )
        return None

    try:
        import httpx
    except ImportError:
        logger.error("httpx not installed. Run: pip install httpx")
        return None

    logger.info(f"Collecting tweets: query='{query}' max={max_results}")

    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "query": query,
        "max_results": min(max_results, 100),  # API max per page is 100
        "tweet.fields": "created_at,lang,public_metrics,author_id",
        "expansions": "author_id",
    }

    records = []
    next_token = None

    while len(records) < max_results:
        if next_token:
            params["next_token"] = next_token

        try:
            resp = httpx.get(url, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"Twitter API error: {e}")
            break

        tweets = data.get("data", [])
        if not tweets:
            break

        for tweet in tweets:
            # Strip @mentions and URLs before storing — privacy + noise reduction
            text = _sanitize_tweet(tweet["text"])
            if len(text.strip()) < 5:
                continue

            records.append({
                "id": str(uuid.uuid4()),
                "twitter_id": tweet["id"],   # keep for dedup, never expose
                "text": text,
                "language": tweet.get("lang", "auto"),
                "source": source_tag,
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "metrics": tweet.get("public_metrics", {}),
            })

        next_token = data.get("meta", {}).get("next_token")
        if not next_token or len(records) >= max_results:
            break

    if not records:
        logger.warning("No tweets collected.")
        return None

    batch_id = f"twitter_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_path = RAW_DIR / f"{batch_id}.jsonl"

    with open(out_path, "w") as f:
        for r in records[:max_results]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    _write_manifest(
        batch_id, source_tag, len(records),
        {"query": query, "max_results": max_results}
    )
    logger.success(f"Collected {len(records)} tweets → {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# 3. Plain text list ingestion
# ---------------------------------------------------------------------------

def collect_texts(
    texts: list[str],
    source_tag: str = "manual",
    language: str = "auto",
) -> Path:
    """
    Ingest a plain list of strings. Useful for quick pilots and testing.
    """
    records = [
        {
            "id": str(uuid.uuid4()),
            "text": t.strip(),
            "language": language,
            "source": source_tag,
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }
        for t in texts
        if t.strip()
    ]

    batch_id = f"{source_tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_path = RAW_DIR / f"{batch_id}.jsonl"

    with open(out_path, "w") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    _write_manifest(batch_id, source_tag, len(records), {})
    logger.success(f"Collected {len(records)} texts → {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# 4. Load a raw JSONL batch for annotation export
# ---------------------------------------------------------------------------

def load_raw_batch(path: str | Path) -> list[dict]:
    """Load a JSONL file from data/raw/ for inspection or annotation export."""
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def export_for_annotation(
    batch_paths: list[str | Path],
    out_path: str | Path = "data/processed/for_annotation.csv",
) -> Path:
    """
    Merge one or more raw batches into a clean CSV ready for Label Studio import.
    Only exports: id, text, language, source.
    Strips all raw metadata to minimise PII in the annotation tool.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_records = []
    for p in batch_paths:
        all_records.extend(load_raw_batch(p))

    # Deduplicate by text
    seen: set[str] = set()
    deduped = []
    for r in all_records:
        if r["text"] not in seen:
            seen.add(r["text"])
            deduped.append(r)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "text", "language", "source"])
        writer.writeheader()
        for r in deduped:
            writer.writerow({
                "id": r["id"],
                "text": r["text"],
                "language": r.get("language", "auto"),
                "source": r.get("source", "unknown"),
            })

    logger.success(f"Exported {len(deduped)} records for annotation → {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize_tweet(text: str) -> str:
    """Strip URLs and @mentions from tweet text before storage."""
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sauti data collector")
    sub = parser.add_subparsers(dest="cmd")

    csv_p = sub.add_parser("csv", help="Ingest a CSV file")
    csv_p.add_argument("filepath")
    csv_p.add_argument("--col", default="text")
    csv_p.add_argument("--tag", default="csv_upload")

    tw_p = sub.add_parser("twitter", help="Collect tweets")
    tw_p.add_argument("query")
    tw_p.add_argument("--max", type=int, default=100)

    txt_p = sub.add_parser("texts", help="Ingest plain texts from file (one per line)")
    txt_p.add_argument("filepath")
    txt_p.add_argument("--tag", default="manual")
    txt_p.add_argument("--lang", default="auto")

    args = parser.parse_args()

    if args.cmd == "csv":
        collect_csv(args.filepath, text_column=args.col, source_tag=args.tag)
    elif args.cmd == "twitter":
        collect_twitter(args.query, max_results=args.max)
    elif args.cmd == "texts":
        with open(args.filepath) as f:
            lines = [l.strip() for l in f if l.strip()]
        collect_texts(lines, source_tag=args.tag, language=args.lang)
    else:
        parser.print_help()
