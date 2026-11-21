"""Parse final answers, stated confidences and verdicts from raw model text."""
from __future__ import annotations

import re

_ANSWER = re.compile(r"ANSWER\s*:\s*\**\s*\$?\s*(?:\\boxed\{)?\s*(-?\d[\d,]*)\s*\}?\s*\$?", re.IGNORECASE)
_CONF = re.compile(r"CONFIDENCE\s*:\s*\**\s*(\d{1,3})\s*%?", re.IGNORECASE)
_VERDICT = re.compile(r"VERDICT\s*:\s*\**\s*(CORRECT|INCORRECT)", re.IGNORECASE)


def parse_answer(text: str) -> int | None:
    """Integer in the last 'ANSWER:' line, commas removed; None if absent."""
    found = _ANSWER.findall(text or "")
    if not found:
        return None
    return int(found[-1].replace(",", ""))


def parse_confidence(text: str) -> int | None:
    found = _CONF.findall(text or "")
    if not found:
        return None
    return max(0, min(100, int(found[-1])))


def parse_verdict(text: str) -> bool | None:
    """True for CORRECT, False for INCORRECT (last occurrence), None if absent."""
    found = _VERDICT.findall(text or "")
    if not found:
        return None
    return found[-1].upper() == "CORRECT"
