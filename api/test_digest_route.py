"""Feature 010 (issue #8) — POST /api/digest route: wiring + error mapping.

No network: extract_from_url and digest_text are monkeypatched on the index module.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import index
from digest import Digest, DigestApiError, DigestConfigError, DigestParseError
from extract import EmptyExtractionError, ExtractedArticle, FetchError, NotHtmlError

client = TestClient(index.app, raise_server_exceptions=False)

ARTICLE = ExtractedArticle(title="A Readable Title", text="Long enough article text. " * 20)
DIGEST = Digest(
    summary="A concise summary of the article.",
    key_points=["First takeaway", "Second takeaway"],
    tags=["testing", "fastapi"],
    category="Engineering",
)
URL = "https://example.com/some-article"
EXPECTED_KEYS = {"id", "url", "title", "summary", "keyPoints", "tags", "category", "createdAt"}


@pytest.fixture
def happy_wiring(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(index, "extract_from_url", lambda url: ARTICLE)
    monkeypatch.setattr(index, "digest_text", lambda text, title=None: DIGEST)
    # Feature 011: the route persists the card; storage behavior is specced in
    # test_cards_routes.py — here it is a no-op.
    monkeypatch.setattr(index, "insert_card", lambda card: None)


def post_digest(url: object = URL) -> "TestClient.response_class":  # type: ignore[name-defined]
    return client.post("/api/digest", json={"url": url})


# --- happy path ---------------------------------------------------------------


def test_happy_path_returns_card_with_exact_camelcase_keys(happy_wiring: None) -> None:
    response = post_digest()
    assert response.status_code == 200
    card = response.json()
    assert set(card.keys()) == EXPECTED_KEYS


def test_happy_path_card_contents(happy_wiring: None) -> None:
    card = post_digest().json()
    assert card["url"] == URL
    assert card["title"] == ARTICLE.title
    assert card["summary"] == DIGEST.summary
    assert card["keyPoints"] == DIGEST.key_points  # snake_case -> camelCase mapping
    assert card["tags"] == DIGEST.tags
    assert card["category"] == DIGEST.category


def test_happy_path_id_is_uuid4(happy_wiring: None) -> None:
    card = post_digest().json()
    parsed = uuid.UUID(card["id"])  # raises ValueError if not a UUID
    assert parsed.version == 4


def test_happy_path_created_at_is_utc_iso8601(happy_wiring: None) -> None:
    card = post_digest().json()
    parsed = datetime.fromisoformat(card["createdAt"])
    assert parsed.tzinfo is not None
    assert parsed.utcoffset().total_seconds() == 0  # type: ignore[union-attr]
    age = abs((datetime.now(timezone.utc) - parsed).total_seconds())
    assert age < 60


def test_digest_receives_extracted_text_and_title(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_digest(text: str, title: str | None = None) -> Digest:
        seen["text"] = text
        seen["title"] = title
        return DIGEST

    monkeypatch.setattr(index, "extract_from_url", lambda url: ARTICLE)
    monkeypatch.setattr(index, "digest_text", fake_digest)
    monkeypatch.setattr(index, "insert_card", lambda card: None)
    assert post_digest().status_code == 200
    assert seen == {"text": ARTICLE.text, "title": ARTICLE.title}


# --- error mapping ------------------------------------------------------------


def _raise(exc: Exception):
    def raiser(*args: object, **kwargs: object) -> object:
        raise exc

    return raiser


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (FetchError(), 502),
        (NotHtmlError(), 422),
        (EmptyExtractionError(), 422),
    ],
    ids=["fetch-502", "not-html-422", "empty-extraction-422"],
)
def test_extraction_errors_map_to_status_with_detail(
    monkeypatch: pytest.MonkeyPatch, error: Exception, status: int
) -> None:
    monkeypatch.setattr(index, "extract_from_url", _raise(error))
    response = post_digest()
    assert response.status_code == status
    assert response.json() == {"detail": error.message}  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (DigestConfigError("The AI service is not configured."), 500),
        (DigestApiError("The AI service returned an error.", status=503), 502),
        (DigestParseError("The AI returned an unreadable digest."), 502),
    ],
    ids=["config-500", "api-502", "parse-502"],
)
def test_digest_errors_map_to_status_with_detail(
    monkeypatch: pytest.MonkeyPatch, error: Exception, status: int
) -> None:
    monkeypatch.setattr(index, "extract_from_url", lambda url: ARTICLE)
    monkeypatch.setattr(index, "digest_text", _raise(error))
    response = post_digest()
    assert response.status_code == status
    assert response.json() == {"detail": str(error)}


# --- request validation -------------------------------------------------------


@pytest.mark.parametrize(
    "body",
    [
        {},  # missing url
        {"url": ""},  # empty
        {"url": "   "},  # whitespace-only
        {"url": "ftp://example.com/file"},  # wrong scheme
        {"url": "not-a-url"},  # scheme-less
        {"url": 42},  # wrong type
    ],
    ids=["missing", "empty", "whitespace", "ftp-scheme", "schemeless", "non-string"],
)
def test_invalid_request_body_returns_422(body: dict[str, object]) -> None:
    response = client.post("/api/digest", json=body)
    assert response.status_code == 422
