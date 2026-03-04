"""
Hybrid language detection for WhatsApp messages.

Detection strategy (fastest match wins):
1. Keyword heuristic — check for Hinglish trigger words
2. Unicode script detection — Devanagari, Tamil, Telugu, Kannada, Bengali
3. langdetect fallback — for ambiguous Latin-script inputs
"""
import re
from dataclasses import dataclass
from typing import Optional

# --- Hinglish keywords (transliterated Hindi commonly used in WhatsApp) ---
HINDI_KEYWORDS = {
    # Catalog actions
    "rakh do", "rakh de", "set karo", "laga do", "add karo", "daal do",
    "hata do", "hata de", "nikal do", "remove karo", "delete karo",
    "badal do", "badal de", "change karo", "update karo",
    # Common Hindi words in inventory context
    "kilo", "packet", "bori", "piece", "rupees", "rupaye", "mein",
    "ka", "ki", "ke", "wala", "wali", "chahiye", "hai", "hain",
    "karo", "karna", "karein", "kaise", "kya", "aur", "bhi",
    "sab", "kitna", "kitne", "price", "daam",
    # Stock phrases
    "aa gaye", "aa gaya", "khatam ho gaya", "khatam", "out of stock",
    "stock mein", "nahi hai",
}

# Minimum keyword matches to classify as Hinglish
HINDI_KEYWORD_THRESHOLD = 2

# Unicode script ranges
SCRIPT_RANGES = {
    "hi": r"[\u0900-\u097F]",   # Devanagari
    "ta": r"[\u0B80-\u0BFF]",   # Tamil
    "te": r"[\u0C00-\u0C7F]",   # Telugu
    "kn": r"[\u0C80-\u0CFF]",   # Kannada
    "bn": r"[\u0980-\u09FF]",   # Bengali
}


@dataclass
class LangResult:
    lang_code: str       # "hi", "en", "ta", "te", "kn", "bn"
    confidence: float    # 0.0 - 1.0
    method: str          # "keyword", "script", "langdetect", "default"


def detect(text: str) -> LangResult:
    """Detect language using a 3-step hybrid strategy."""
    if not text or not text.strip():
        return LangResult(lang_code="en", confidence=0.0, method="default")

    text_lower = text.lower().strip()

    # --- Step 1: Keyword heuristic for Hinglish ---
    matches = 0
    for kw in HINDI_KEYWORDS:
        if kw in text_lower:
            matches += 1
        if matches >= HINDI_KEYWORD_THRESHOLD:
            return LangResult(lang_code="hi", confidence=0.9, method="keyword")

    # --- Step 2: Unicode script detection ---
    for lang_code, pattern in SCRIPT_RANGES.items():
        if re.search(pattern, text):
            return LangResult(lang_code=lang_code, confidence=0.95, method="script")

    # --- Step 3: langdetect fallback ---
    try:
        from langdetect import detect as ld_detect, DetectorFactory
        DetectorFactory.seed = 0  # deterministic
        detected = ld_detect(text)

        # Map langdetect codes to our codes
        LANG_MAP = {
            "hi": "hi", "en": "en", "ta": "ta", "te": "te",
            "kn": "kn", "bn": "bn", "mr": "hi",  # Marathi → Hindi fallback
            "gu": "hi",  # Gujarati → Hindi fallback
        }
        lang = LANG_MAP.get(detected, "en")
        return LangResult(lang_code=lang, confidence=0.7, method="langdetect")
    except Exception:
        pass

    # --- Default ---
    return LangResult(lang_code="en", confidence=0.5, method="default")
