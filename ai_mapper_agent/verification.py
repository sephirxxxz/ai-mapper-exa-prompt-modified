from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class RegexVerification:
    matched: bool
    excerpt: str
    match_start: int | None = None
    match_end: int | None = None


def verify_regex_claim(page_text: str, pattern: str, *, excerpt_radius: int = 160) -> RegexVerification:
    """Verify a declared claim against fetched page text without inferring missing facts."""
    match = re.search(pattern, page_text, flags=re.IGNORECASE)
    if match is None:
        return RegexVerification(matched=False, excerpt="")
    start = max(0, match.start() - excerpt_radius)
    end = min(len(page_text), match.end() + excerpt_radius)
    return RegexVerification(
        matched=True,
        excerpt=page_text[start:end].strip(),
        match_start=match.start(),
        match_end=match.end(),
    )
