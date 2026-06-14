"""Feature 019 — find related cards already on the board, ranked by meaning.

One OpenRouter chat-completion call (Variant A): given a target card and the other
cards on the board, the model returns up to 3 most-related candidate ids with a
one-line reason. Code filters returned ids to the real candidate set, dedupes, and
caps at 3, so a hallucinated id can never reach the client. Errors are typed and
`str()`-safe to show the user (PRD: never a broken state).

Scope is deliberately the user's own board — no web search, no embeddings. Swapping
this module for an embeddings/pgvector backend later is a local change (P2).
"""

from __future__ import annotations

import json
import os
import re

import httpx
from pydantic import BaseModel, ValidationError

# Reuse the OpenRouter wiring constants from the digest module (same provider).
from digest import (
    ALLOWED_LANGUAGES,
    DEFAULT_MODEL,
    OPENROUTER_URL,
    REQUEST_TIMEOUT_SECONDS,
)

_LANGUAGE_NAMES = {"uk": "Ukrainian", "ru": "Russian", "en": "English"}
MAX_RESULTS = 3
_SUMMARY_BUDGET = 280  # trim each card's summary to bound prompt size/cost
_CODE_FENCE_RE = re.compile(r"^```[a-zA-Z0-9_-]*\s*\n?(.*?)\n?```\s*$", re.DOTALL)


def _strip_code_fences(content: str) -> str:
    """Drop a surrounding ```json fence — models wrap strict JSON despite asking not to."""
    match = _CODE_FENCE_RE.match(content.strip())
    return match.group(1) if match else content.strip()


class SimilarError(Exception):
    """Base error; str(error) is a user-displayable message."""


class SimilarConfigError(SimilarError):
    """OPENROUTER_API_KEY missing."""


class SimilarApiError(SimilarError):
    """The AI call failed (network or non-2xx)."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class SimilarParseError(SimilarError):
    """The AI returned something we could not parse into refs."""


class SimilarRef(BaseModel):
    """A related card the model picked: an id from the board + why it's related."""

    id: str
    reason: str

    model_config = {"frozen": True}


class _SimilarResponse(BaseModel):
    similar: list[SimilarRef]


def _trim(text: str) -> str:
    return text if len(text) <= _SUMMARY_BUDGET else text[:_SUMMARY_BUDGET] + "…"


def build_similar_prompt(
    target: dict, others: list[dict], language: str
) -> tuple[str, str]:
    """System + user prompt for the similarity ranking. Pure helper.

    Raises ValueError for a language outside ALLOWED_LANGUAGES.
    """
    if language not in ALLOWED_LANGUAGES:
        raise ValueError(
            f"Unsupported language {language!r}; allowed: {', '.join(ALLOWED_LANGUAGES)}."
        )
    lang_name = _LANGUAGE_NAMES[language]
    system = (
        "You help a reader find which of their saved article cards are most related to a "
        "target card, by topic and meaning. Respond with STRICT JSON only — a single object "
        'with one key "similar": an array of at most 3 objects, each with exactly two keys: '
        '"id" (the id of a candidate card, copied verbatim) and "reason" (one short sentence '
        f"in {lang_name} saying why it is related). Order from most to least related. Use ONLY "
        "ids from the provided candidates. If none are genuinely related, return an empty array."
    )
    candidates = [
        {"id": c["id"], "title": c["title"], "summary": _trim(c["summary"]), "tags": c["tags"]}
        for c in others
    ]
    user = (
        "TARGET CARD:\n"
        + json.dumps(
            {"title": target["title"], "summary": _trim(target["summary"]),
             "tags": target["tags"]},
            ensure_ascii=False,
        )
        + "\n\nCANDIDATE CARDS:\n"
        + json.dumps(candidates, ensure_ascii=False)
    )
    return system, user


def find_similar(
    target: dict,
    others: list[dict],
    *,
    language: str = "uk",
    client: httpx.Client | None = None,
) -> list[SimilarRef]:
    """Rank `others` by relatedness to `target` via one OpenRouter call.

    Returns 0–MAX_RESULTS refs whose ids exist in `others` (deduped, order
    preserved). No AI call is made when `others` is empty. `client` is injectable
    for tests. Raises ValueError (bad language) / SimilarConfigError /
    SimilarApiError / SimilarParseError.
    """
    system, user = build_similar_prompt(target, others, language)  # validates language
    if not others:
        return []

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise SimilarConfigError(
            "The AI service is not configured (missing OPENROUTER_API_KEY)."
        )

    payload = {
        "model": os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "provider": {"sort": "latency"},
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    owns_client = client is None
    http = client or httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS)
    try:
        response = http.post(OPENROUTER_URL, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise SimilarApiError(
            "Could not reach the AI service. Check your connection and try again."
        ) from exc
    finally:
        if owns_client:
            http.close()

    if response.status_code >= 400:
        raise SimilarApiError(
            f"The AI service returned an error (HTTP {response.status_code}). Please try again.",
            status=response.status_code,
        )

    try:
        content = response.json()["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise TypeError("message content is not a string")
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise SimilarParseError(
            "The AI service returned an unexpected response. Please try again."
        ) from exc

    try:
        parsed = _SimilarResponse.model_validate_json(_strip_code_fences(content))
    except ValidationError as exc:
        raise SimilarParseError(
            "The AI returned an unreadable list of related cards. Please try again."
        ) from exc

    valid_ids = {c["id"] for c in others}
    seen: set[str] = set()
    result: list[SimilarRef] = []
    for ref in parsed.similar:
        if ref.id in valid_ids and ref.id not in seen:
            seen.add(ref.id)
            result.append(ref)
        if len(result) == MAX_RESULTS:
            break
    return result
