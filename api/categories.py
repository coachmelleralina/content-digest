"""Category normalization on the save path (feature 020, issue #12).

Faithful Python port of app/src/lib/categories.ts (feature 002): merges
near-duplicate AI-chosen labels into existing sections. Rules and priority
order are identical; test_categories.py mirrors categories.spec.ts to keep
the two implementations in sync.
"""

from __future__ import annotations

import re


def _collapse(raw: str) -> str:
    return re.sub(r"\s+", " ", raw.strip())


def _fold(raw: str) -> str:
    return _collapse(re.sub(r"[-_]", " ", raw)).lower()


def _singular_fold(folded: str) -> str:
    """Trailing-s plural fold on the last word; words shorter than 4 chars are
    left alone so labels like "AI" or "iOS" are never mangled."""
    words = folded.split(" ")
    last = words[-1]
    if len(last) >= 4 and last.endswith("s"):
        words[-1] = last[:-1]
    return " ".join(words)


def _initials(folded: str) -> str | None:
    words = folded.split(" ")
    if len(words) < 2:
        return None
    return "".join(word[0] for word in words)


def _levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        curr = [i]
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[len(b)]


def _typo_matches(a: str, b: str) -> bool:
    if len(a) < 5 or len(b) < 5:
        return False
    threshold = 2 if min(len(a), len(b)) >= 8 else 1
    return _levenshtein(a, b) <= threshold


def resolve_category(raw: str, existing: list[str]) -> str:
    """Given an AI-proposed category label and the labels already stored,
    returns the label to file the card under: an existing label when the new
    one is a near-duplicate (case/whitespace, plural, acronym, single typo),
    otherwise the cleaned-up new label."""
    cleaned = _collapse(raw)
    if cleaned == "":
        return "Uncategorized"
    folded = _fold(raw)

    rules = [
        lambda e: _fold(e) == folded,
        lambda e: _singular_fold(_fold(e)) == _singular_fold(folded),
        lambda e: _initials(_fold(e)) == folded or _initials(folded) == _fold(e),
        lambda e: _typo_matches(_fold(e), folded),
    ]
    for matches in rules:
        hit = next((e for e in existing if matches(e)), None)
        if hit is not None:
            return hit
    return cleaned
