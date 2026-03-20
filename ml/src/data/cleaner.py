"""
cleaner.py — Text normalization for East African social media content.

Handles:
- Swahili / English / Sheng code-switching
- Common Sheng contractions and slang normalization
- URL, mention, hashtag stripping (configurable)
- Repeated character normalization (e.g. "saaaana" → "sana")
- Unicode normalization
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Sheng normalization map
# Expand as the community contributes more terms.
# Format: { sheng_term: standard_sw_or_en_equivalent }
# ---------------------------------------------------------------------------
SHENG_NORMALIZATION: dict[str, str] = {
    "mtoi": "mtoto",        # child
    "msee": "mtu",          # person/guy
    "dem": "msichana",      # girl
    "manze": "rafiki",      # friend/man
    "poa": "sawa",          # okay/cool
    "fiti": "vizuri",       # fine/good
    "malo": "mahali",       # place
    "kadaa": "kadhalika",   # likewise/also
    "ndio": "ndiyo",        # yes (variant)
    "naez": "naweza",       # I can
    "siwezi": "siwezi",     # I cannot (already standard)
    "klist": "Kilimani",    # neighbourhood
    "nganya": "matatu",     # minibus
    "mse": "mtu",           # person
    "hao": "wao",           # they/them
    "kunywa": "kunywa",     # drink (standard)
    "kucheza": "kucheza",   # play (standard)
}

# Patterns that signal potential harmful intent — used downstream for feature engineering
THREAT_PATTERNS: list[str] = [
    r"tutakukumbuka",
    r"utaona\b",
    r"tutaonana\b",
    r"usisahau\b",
    r"we'll find you",
    r"you'll (pay|regret|see)",
    r"i know where you",
]


@dataclass
class CleanerConfig:
    remove_urls: bool = True
    remove_mentions: bool = True          # @handles
    remove_hashtags: bool = False         # keep hashtags — often carry context
    normalize_sheng: bool = True
    normalize_repeated_chars: bool = True
    max_repeated_chars: int = 2           # "saaaana" → "saana" (keeps 2 max)
    lowercase: bool = False               # do NOT lowercase by default — casing carries meaning
    strip_emoji: bool = False             # keep emoji — they carry strong sentiment signal
    min_length: int = 3                   # discard posts shorter than this after cleaning
    flag_threat_patterns: bool = True


class TextCleaner:
    def __init__(self, config: Optional[CleanerConfig] = None):
        self.config = config or CleanerConfig()
        self._compiled_threats = [
            re.compile(p, re.IGNORECASE) for p in THREAT_PATTERNS
        ]

    def clean(self, text: str) -> dict:
        """
        Clean a single text string.

        Returns:
            {
                "original": str,
                "cleaned": str,
                "flags": list[str],   # e.g. ["threat_pattern_detected"]
                "too_short": bool
            }
        """
        if not text or not text.strip():
            return {"original": text, "cleaned": "", "flags": [], "too_short": True}

        original = text
        flags: list[str] = []

        # Unicode normalization (handles Arabic numerals, diacritics, etc.)
        text = unicodedata.normalize("NFC", text)

        # Flag threat patterns before stripping anything
        if self.config.flag_threat_patterns:
            for pattern in self._compiled_threats:
                if pattern.search(text):
                    flags.append("threat_pattern_detected")
                    break

        # Remove URLs
        if self.config.remove_urls:
            text = re.sub(r"https?://\S+|www\.\S+", " ", text)

        # Remove @mentions
        if self.config.remove_mentions:
            text = re.sub(r"@\w+", " ", text)

        # Remove hashtags (symbol only, keep word)
        if self.config.remove_hashtags:
            text = re.sub(r"#(\w+)", r"\1", text)

        # Normalize Sheng terms
        if self.config.normalize_sheng:
            tokens = text.split()
            normalized = []
            for token in tokens:
                lower_token = token.lower()
                if lower_token in SHENG_NORMALIZATION:
                    normalized.append(SHENG_NORMALIZATION[lower_token])
                    flags.append("sheng_normalized")
                else:
                    normalized.append(token)
            text = " ".join(normalized)

        # Normalize repeated characters: "saaaana" → "saana"
        if self.config.normalize_repeated_chars:
            n = self.config.max_repeated_chars
            text = re.sub(r"(.)\1{" + str(n) + r",}", r"\1" * n, text)

        # Lowercase
        if self.config.lowercase:
            text = text.lower()

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        too_short = len(text) < self.config.min_length

        return {
            "original": original,
            "cleaned": text,
            "flags": list(set(flags)),
            "too_short": too_short,
        }

    def clean_batch(self, texts: list[str]) -> list[dict]:
        """Clean a list of texts. Skips empty strings."""
        return [self.clean(t) for t in texts]


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cleaner = TextCleaner()

    samples = [
        "Wote Somali ni terrorists na wezi saaaana!",
        "Tutakukumbuka baada ya uchaguzi hii @user123",
        "Poa msee, tutaonana malo",
        "https://t.co/abc123 check this out",
        "Wewe ni mjinga kabisaaa",
    ]

    for s in samples:
        result = cleaner.clean(s)
        print(f"IN:    {result['original']}")
        print(f"OUT:   {result['cleaned']}")
        print(f"FLAGS: {result['flags']}")
        print()
