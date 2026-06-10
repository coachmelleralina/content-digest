"""Feature 009 (issue #7) — text → {summary, key_points, tags, category} via OpenRouter.

One chat-completion call per digest (ADR 004). Pure-ish module: takes text, returns a
validated `Digest` or raises a typed error whose `str()` is safe to show to the user
(PRD: never a blank/broken card). Route wiring happens in issue #8.

Config (env):
- OPENROUTER_API_KEY — required, server-side only.
- OPENROUTER_MODEL   — optional; defaults to DEFAULT_MODEL (one-line/env swap, ADR 004).
"""

from __future__ import annotations

import json
import os
import re

import httpx
from pydantic import BaseModel, Field, ValidationError, field_validator

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-3.5-haiku"
MAX_INPUT_CHARS = 12_000  # bound prompt size → bound cost
REQUEST_TIMEOUT_SECONDS = 60.0

_CODE_FENCE_RE = re.compile(r"^```[a-zA-Z0-9_-]*\s*\n?(.*?)\n?```\s*$", re.DOTALL)

_SYSTEM_PROMPT = (
    "You summarize articles. Respond with STRICT JSON only — a single JSON object, "
    "no markdown, no code fences, no commentary. The object must have exactly these keys:\n"
    '- "summary": string, 2-3 sentence summary of the article;\n'
    '- "key_points": array of 1 to 8 short strings, the main takeaways;\n'
    '- "tags": array of 1 to 6 short lowercase topic tags;\n'
    '- "category": string, a single short free-form topic label of your choosing '
    "(e.g. a board section name), one line, no newlines."
)


class DigestError(Exception):
    """Base class for digest failures. str(error) is a user-displayable message."""


class DigestConfigError(DigestError):
    """Server misconfiguration (e.g. missing OPENROUTER_API_KEY)."""


class DigestParseError(DigestError):
    """The model's output could not be parsed into a valid Digest."""


class DigestApiError(DigestError):
    """OpenRouter HTTP/network failure. `status` is the HTTP status, if any."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class Digest(BaseModel):
    """Structured digest of one article (ADR 004). Category is free-form, AI-chosen."""

    summary: str
    key_points: list[str] = Field(min_length=1, max_length=8)
    tags: list[str] = Field(min_length=1, max_length=6)
    category: str

    @field_validator("summary")
    @classmethod
    def _summary_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("summary must be a non-empty string")
        return value.strip()

    @field_validator("category")
    @classmethod
    def _category_non_empty_single_line(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("category must be a non-empty string")
        if "\n" in stripped or "\r" in stripped:
            raise ValueError("category must be a single line")
        return stripped


def truncate_text(text: str, limit: int = MAX_INPUT_CHARS) -> str:
    """Cap input text length to bound prompt size/cost. Pure helper."""
    return text if len(text) <= limit else text[:limit]


def build_user_prompt(text: str, title: str | None = None) -> str:
    """Build the user message: optional title + (truncated) article text. Pure helper."""
    body = truncate_text(text)
    if title:
        return f"Title: {title}\n\nArticle text:\n{body}"
    return f"Article text:\n{body}"


def _strip_code_fences(content: str) -> str:
    """Remove a surrounding markdown code fence (``` / ```json) if present."""
    match = _CODE_FENCE_RE.match(content.strip())
    return match.group(1) if match else content.strip()


def _parse_digest(content: str) -> Digest:
    """Parse model output (strict JSON, fences tolerated) into a validated Digest."""
    raw = _strip_code_fences(content)
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise DigestParseError(
            "The AI returned an unreadable digest. Please try again."
        ) from exc
    try:
        return Digest.model_validate(data)
    except ValidationError as exc:
        raise DigestParseError(
            "The AI returned an incomplete digest. Please try again."
        ) from exc


def digest_text(
    text: str,
    title: str | None = None,
    *,
    client: httpx.Client | None = None,
) -> Digest:
    """Digest article text via ONE OpenRouter chat-completion call.

    `client` is injectable for tests (httpx.MockTransport); production uses a real
    httpx.Client. Raises DigestConfigError / DigestApiError / DigestParseError.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise DigestConfigError(
            "The AI service is not configured (missing OPENROUTER_API_KEY). "
            "Set it in the server environment."
        )

    payload = {
        "model": os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL),
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(text, title)},
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    owns_client = client is None
    http = client or httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS)
    try:
        response = http.post(OPENROUTER_URL, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise DigestApiError(
            "Could not reach the AI service. Check your connection and try again."
        ) from exc
    finally:
        if owns_client:
            http.close()

    if response.status_code >= 400:
        raise DigestApiError(
            f"The AI service returned an error (HTTP {response.status_code}). "
            "Please try again.",
            status=response.status_code,
        )

    try:
        content = response.json()["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise TypeError("message content is not a string")
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise DigestParseError(
            "The AI service returned an unexpected response. Please try again."
        ) from exc

    return _parse_digest(content)
