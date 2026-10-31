from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal

_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

@dataclass(frozen=True)
class Result:
    ok: bool                 # did the entity survive the round trip?
    kind: str                # match | not_found | length_mismatch | substitution | wrong_value
    expected: str            # what we said
    heard: str | None        # what we extracted from the transcript

def normalize(text: str) -> str:
    """
    Normalize text for comparison:
    - convert Devanagari digits to ASCII digits
    - normalize Unicode to NFKC
    - replace "|" with space (for Google TTS)
    - collapse whitespace
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_DEVANAGARI_DIGITS)
    text = text.replace("|", " ")
    text = re.sub(r"\s+", " ", text)  
    return text.strip()

# digit strings: phone numbers, pin codes, IDs
def _longest_digit_run(text: str) -> str | None:
    runs = re.findall(r"\d(?:[\s\-]?\d)+", text)
    if not runs:
        return None
    digits = [re.sub(r"\D", "", r) for r in runs]
    return max(digits, key=len)

def compare_digits(expected: str, heard_text: str) -> Result:
    exp = re.sub(r"\D", "", expected)
    got = _longest_digit_run(normalize(heard_text))
    if got is None:
        return Result(False, "not_found", exp, None)
    if got != exp and got.endswith(exp) and got[: len(got) - len(exp)] in ("91", "0"):
        got = exp          # tolerate +91 / leading 0
    if got == exp:
        return Result(True, "match", exp, got)
    if len(got) != len(exp):
        return Result(False, "length_mismatch", exp, got)
    return Result(False, "substitution", exp, got)

# rupee amounts
_AMOUNT_WITH_SYMBOL = re.compile(r"(?:₹|rs\.?|inr)\s*(\d[\d,]*(?:\.\d+)?)", re.IGNORECASE)
_ANY_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")

def compare_amount(expected: int | str, heard_text: str) -> Result:
    exp = Decimal(str(expected))
    text = normalize(heard_text)
    m = _AMOUNT_WITH_SYMBOL.search(text)
    if m: 
        raw = m.group(1)
    else:
        n = _ANY_NUMBER.search(text)
        raw = n.group(0) if n else None
    if raw is None:
        return Result(False, "not_found", str(exp), None)
    got = Decimal(raw.replace(",", "").rstrip("."))
    if got == exp:
        return Result(True, "match", str(exp), str(got))
    return Result(False, "wrong_value", str(exp), str(got))

# clock times
_TIME = re.compile(r"(\d{1,2})\s*[:.]\s*(\d{2})")


def compare_time(expected: tuple[int, int], heard_text: str) -> Result:
    exp_h, exp_m = expected
    exp_str = f"{exp_h:02d}:{exp_m:02d}"
    m = _TIME.search(normalize(heard_text))
    if not m:
        return Result(False, "not_found", exp_str, None)
    got_h, got_m = int(m.group(1)), int(m.group(2))
    got_str = f"{got_h:02d}:{got_m:02d}"
    if got_m == exp_m and got_h % 12 == exp_h % 12:
        return Result(True, "match", exp_str, got_str)
    return Result(False, "wrong_value", exp_str, got_str)
