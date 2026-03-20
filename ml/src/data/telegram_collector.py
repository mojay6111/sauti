"""
telegram_collector.py — Collect messages from public Kenyan Telegram channels.

Targets public channels only — no private groups, no DMs.
All collected data lands in data/raw/ with provenance manifest.

Usage:
    python ml/src/data/telegram_collector.py

First run will ask for your phone number and a verification code
from Telegram — this is normal, it creates a session file.
After first run, it connects automatically.
"""

import asyncio
import csv
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Kenyan public channels — all public, no private groups
# Add more as you discover them
# ---------------------------------------------------------------------------
KENYAN_CHANNELS = [
    # News
    "KBCChannel1",
    "ntvkenya",
    "CitizenTVKenya",

    # Politics & commentary
    "kenyanpolitics254",
    "nairobinews254",

    # General Kenya
    "Kenya254News",
    "KenyaUpdates",

    # Add your own discovered channels here
]

# How many messages to pull per channel
MESSAGES_PER_CHANNEL = 200


async def collect_channel(client, channel_username: str) -> list[dict]:
    """Pull recent messages from a single public channel."""
    records = []

    try:
        entity = await client.get_entity(channel_username)
        channel_name = getattr(entity, "title", channel_username)
        logger.info(f"Collecting from: {channel_name} (@{channel_username})")

        async for message in client.iter_messages(entity, limit=MESSAGES_PER_CHANNEL):
            # Skip empty messages, stickers, photos with no caption
            if not message.text or not message.text.strip():
                continue

            text = clean_telegram_text(message.text)
            if len(text) < 10:
                continue

            records.append({
                "id": str(uuid.uuid4()),
                "text": text,
                "language": "auto",
                "source": f"telegram_{channel_username}",
                "channel": channel_name,
                "message_date": message.date.isoformat() if message.date else None,
                "collected_at": datetime.now(timezone.utc).isoformat(),
                # Never store message ID or user ID — privacy
            })

        logger.success(f"  Collected {len(records)} messages from @{channel_username}")

    except Exception as e:
        logger.warning(f"  Could not collect @{channel_username}: {e}")

    return records


def clean_telegram_text(text: str) -> str:
    """Remove Telegram formatting, links, and excess whitespace."""
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove @mentions
    text = re.sub(r"@\w+", "", text)
    # Remove Telegram channel links like t.me/xxx
    text = re.sub(r"t\.me/\S+", "", text)
    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse whitespace
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def write_manifest(batch_id: str, channels: list[str], count: int):
    manifest = {
        "batch_id": batch_id,
        "source": "telegram",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "record_count": count,
        "channels": channels,
        "privacy_note": (
            "Public Telegram channel messages only. "
            "No user IDs, no message IDs stored. "
            "Do not share outside annotation team."
        ),
    }
    path = RAW_DIR / f"{batch_id}_manifest.json"
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)


async def run_collector(channels: list[str] = None):
    """Main collector — connects to Telegram and pulls all channels."""
    try:
        from telethon import TelegramClient
        from telethon.errors import FloodWaitError
    except ImportError:
        logger.error("telethon not installed. Run: pip install telethon")
        return

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        logger.error(
            "TELEGRAM_API_ID and TELEGRAM_API_HASH not set in .env\n"
            "Get them from: my.telegram.org → API development tools"
        )
        return

    channels = channels or KENYAN_CHANNELS
    session_path = Path("data/raw/.telegram_session")

    logger.info(f"Connecting to Telegram...")
    logger.info(f"Session file: {session_path}")
    logger.info("First run will ask for your phone number and verification code.")

    client = TelegramClient(str(session_path), int(api_id), api_hash)

    async with client:
        all_records = []
        successful_channels = []

        for channel in channels:
            try:
                records = await collect_channel(client, channel)
                all_records.extend(records)
                if records:
                    successful_channels.append(channel)
                # Be polite to Telegram's servers
                await asyncio.sleep(2)

            except Exception as e:
                logger.warning(f"Skipping @{channel}: {e}")
                continue

        if not all_records:
            logger.warning("No records collected. Check channel names and connectivity.")
            return

        # Write JSONL
        batch_id = f"telegram_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        out_path = RAW_DIR / f"{batch_id}.jsonl"

        with open(out_path, "w", encoding="utf-8") as f:
            for r in all_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        write_manifest(batch_id, successful_channels, len(all_records))

        logger.success(f"\n{'='*50}")
        logger.success(f"Collection complete!")
        logger.success(f"  Total messages: {len(all_records)}")
        logger.success(f"  Channels:       {len(successful_channels)}")
        logger.success(f"  Output:         {out_path}")
        logger.success(f"{'='*50}")
        logger.info(f"\nNext step — export for annotation:")
        logger.info(f"  python -c \"")
        logger.info(f"  from ml.src.data.collector import export_for_annotation")
        logger.info(f"  export_for_annotation(['{out_path}'])\"")

        return out_path


def export_to_csv(jsonl_path: str | Path, out_path: str = None):
    """
    Convert collected JSONL to a clean CSV for annotation.
    Strips all metadata — only keeps id, text, language, source.
    """
    jsonl_path = Path(jsonl_path)
    out_path = Path(out_path or f"data/processed/for_annotation_{datetime.now().strftime('%Y%m%d')}.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                records.append({
                    "id": r["id"],
                    "text": r["text"],
                    "language": r.get("language", "auto"),
                    "source": r.get("source", "telegram"),
                })

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "text", "language", "source"])
        writer.writeheader()
        writer.writerows(records)

    logger.success(f"Exported {len(records)} records → {out_path}")
    return out_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sauti Telegram collector")
    parser.add_argument(
        "--channels", nargs="+",
        help="Channel usernames to collect (without @). Defaults to built-in Kenyan list.",
        default=None
    )
    parser.add_argument(
        "--limit", type=int, default=200,
        help="Messages per channel (default: 200)"
    )
    parser.add_argument(
        "--export", action="store_true",
        help="Also export to CSV for annotation after collecting"
    )
    args = parser.parse_args()

    MESSAGES_PER_CHANNEL = args.limit

    result = asyncio.run(run_collector(args.channels))

    if result and args.export:
        export_to_csv(result)
