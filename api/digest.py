"""Features 009 + 014 (issues #7, #13) — text → ELI5 digest via OpenRouter.

One chat-completion call per digest (ADR 004). Pure-ish module: takes text, returns a
validated `Digest` or raises a typed error whose `str()` is safe to show to the user
(PRD: never a blank/broken card).

Feature 014 rework: `summary` is a simple-words EXPLANATION (like to a child),
`key_points` are {takeaway, quote} objects where the quote is a verbatim source
fragment (verified code-side; hallucinated quotes become None), `tags` are canonical
reusable topics (normalized code-side), and the digest language is uk/ru/en.

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

ALLOWED_LANGUAGES = ("uk", "ru", "en")
_LANGUAGE_NAMES = {"uk": "Ukrainian", "ru": "Russian", "en": "English"}
MAX_TAGS = 4
MAX_TAG_CHARS = 24


def build_system_prompt(language: str) -> str:
    """System prompt for the ELI5 digest (feature 014). Pure helper.

    Raises ValueError for a language outside ALLOWED_LANGUAGES.
    """
    if language not in ALLOWED_LANGUAGES:
        raise ValueError(
            f"Unsupported digest language {language!r}; allowed: {', '.join(ALLOWED_LANGUAGES)}."
        )
    lang_name = _LANGUAGE_NAMES[language]
    return (
        "You explain articles in very simple words, like to a curious child: what the "
        "article is about, why it matters, and which thoughts the reader can take away. "
        "Respond with STRICT JSON only — a single JSON object, no markdown, no code "
        "fences, no commentary. The object must have exactly these keys:\n"
        f'- "summary": string, 2-4 sentences in {lang_name} that EXPLAIN the article in '
        "simple words: what it is about and why it is important. Explain like to a child "
        "— no jargon; if a technical term is unavoidable, explain it in brackets right "
        "after it;\n"
        '- "key_points": array of 3 to 5 objects, each with exactly two keys:\n'
        f'  - "takeaway": string in {lang_name} — one practical thought the reader takes '
        "away for themselves, worded simply;\n"
        '  - "quote": string — a SHORT verbatim fragment (at most 12 words) copied '
        "EXACTLY, character for character, from the article text, grounding this "
        "takeaway. Keep the quote in the article's ORIGINAL language. Do not paraphrase, "
        "do not translate, do not fix typos or punctuation — copy the fragment exactly "
        "as it appears in the text;\n"
        '- "tags": array of 2 to 4 canonical topic tags: each tag is one general '
        'lowercase concept (e.g. "продуктивність", "ai", "здоров\'я") that could be '
        "reused across many different articles. Prefer broad canonical topics over "
        "phrases taken from the text;\n"
        '- "category": string, a single short free-form topic label of your choosing '
        "(e.g. a board section name), one line, no newlines.\n"
        f'Write "summary" and every "takeaway" in {lang_name}. Quotes stay in the '
        "article's original language."
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


class KeyPoint(BaseModel):
    """One grounded takeaway (feature 014). `quote` is a verbatim source fragment;
    it becomes None when code-side verification can't find it in the source text."""

    takeaway: str
    quote: str | None = None

    @field_validator("takeaway")
    @classmethod
    def _takeaway_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("takeaway must be a non-empty string")
        return value.strip()


def normalize_tags(tags: list[str]) -> list[str]:
    """Canonical-tag normalization (feature 014). Pure helper.

    Strip, lowercase, truncate each tag to MAX_TAG_CHARS, drop empties, keep at
    most MAX_TAGS (truncate the list — never reject).
    """
    cleaned = [tag.strip().lower()[:MAX_TAG_CHARS] for tag in tags]
    return [tag for tag in cleaned if tag][:MAX_TAGS]


def _normalize_ws(text: str) -> str:
    """Collapse all whitespace runs to single spaces (for quote matching)."""
    return " ".join(text.split())


def verify_quotes(key_points: list[KeyPoint], source_text: str) -> list[KeyPoint]:
    """Ground-check quotes against the source (feature 014). Pure helper.

    A quote must occur in the source text under whitespace-normalized comparison;
    otherwise it is replaced with None. Takeaways are always kept.
    """
    haystack = _normalize_ws(source_text)
    verified: list[KeyPoint] = []
    for point in key_points:
        quote = point.quote
        if quote is not None and _normalize_ws(quote) not in haystack:
            quote = None
        verified.append(KeyPoint(takeaway=point.takeaway, quote=quote))
    return verified


class Digest(BaseModel):
    """Structured digest of one article (ADR 004 + feature 014).

    Summary is an ELI5 explanation; key_points are grounded {takeaway, quote}
    objects; tags are canonical topics (normalized); category is free-form."""

    summary: str
    key_points: list[KeyPoint] = Field(min_length=1, max_length=8)
    tags: list[str] = Field(min_length=1, max_length=MAX_TAGS)
    category: str

    @field_validator("tags", mode="before")
    @classmethod
    def _normalize_tags(cls, value: object) -> object:
        if isinstance(value, list) and all(isinstance(tag, str) for tag in value):
            return normalize_tags(value)
        return value

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
    language: str = "uk",
    client: httpx.Client | None = None,
) -> Digest:
    """Digest article text via ONE OpenRouter chat-completion call.

    `language` (uk/ru/en, feature 014) selects the explanation/takeaway language;
    quotes stay in the article's original language and are verified against the
    source text (hallucinated quotes become None). `client` is injectable for tests
    (httpx.MockTransport); production uses a real httpx.Client. Raises ValueError
    for an unsupported language, else DigestConfigError / DigestApiError /
    DigestParseError.
    """
    system_prompt = build_system_prompt(language)  # raises ValueError early

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise DigestConfigError(
            "The AI service is not configured (missing OPENROUTER_API_KEY). "
            "Set it in the server environment."
        )

    payload = {
        "model": os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL),
        "messages": [
            {"role": "system", "content": system_prompt},
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

    digest = _parse_digest(content)
    # Feature 014: ground-check quotes against the FULL original text (a superset
    # of the truncated prompt text) — hallucinated quotes become None.
    return digest.model_copy(update={"key_points": verify_quotes(digest.key_points, text)})
