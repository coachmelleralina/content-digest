"""Spec for feature 015 — POST /api/cards/{id}/translate (issue #14).

No network, no live DB: get_card / update_card / extract_from_url / digest_text
are monkeypatched on the index module, same seam style as test_digest_route.py.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import index
from db import DbError
from digest import Digest, DigestApiError, DigestConfigError, DigestParseError, KeyPoint
from extract import EmptyExtractionError, ExtractedArticle, FetchError, NotHtmlError

client = TestClient(index.app, raise_server_exceptions=False)

CARD_ID = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
STORED_CARD = {
    "id": CARD_ID,
    "url": "https://example.com/article",
    "title": "Original Title",
    "summary": "Проста відповідь: стаття про тестування.",
    "keyPoints": [{"takeaway": "Перша думка", "quote": "verbatim fragment"}],
    "tags": ["testing"],
    "category": "Engineering",
    "language": "uk",
    "createdAt": "2026-06-10T09:00:00+00:00",
}
ARTICLE = ExtractedArticle(title="Refreshed Title", text="Long enough article text. " * 20)
EN_DIGEST = Digest(
    summary="Simple answer: this article is about testing.",
    key_points=[
        KeyPoint(takeaway="First thought", quote="Long enough article text."),
        KeyPoint(takeaway="Second thought", quote=None),
    ],
    tags=["testing", "fastapi"],
    category="Engineering",
)
EXPECTED_KEYS = {
    "id",
    "url",
    "title",
    "summary",
    "keyPoints",
    "tags",
    "category",
    "language",
    "createdAt",
}


def post_translate(card_id: str = CARD_ID, **body: object) -> "TestClient.response_class":  # type: ignore[name-defined]
    return client.post(f"/api/cards/{card_id}/translate", json=body or {"language": "en"})


def _raise(exc: Exception):
    def raiser(*args: object, **kwargs: object) -> object:
        raise exc

    return raiser


@pytest.fixture
def happy_wiring(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, dict]]:
    """Wire all seams for a successful uk → en translation; collect update calls."""
    updates: list[tuple[str, dict]] = []
    monkeypatch.setattr(index, "get_card", lambda card_id: dict(STORED_CARD))
    monkeypatch.setattr(index, "extract_from_url", lambda url: ARTICLE)
    monkeypatch.setattr(
        index, "digest_text", lambda text, title=None, language="uk": EN_DIGEST
    )
    monkeypatch.setattr(
        index, "update_card", lambda card_id, card: updates.append((card_id, card))
    )
    return updates


# --- happy path -----------------------------------------------------------------


def test_happy_path_returns_full_card_with_language(happy_wiring: list) -> None:
    response = post_translate()
    assert response.status_code == 200
    card = response.json()
    assert set(card.keys()) == EXPECTED_KEYS
    assert card["language"] == "en"


def test_happy_path_refreshes_digest_fields_and_keeps_identity(happy_wiring: list) -> None:
    card = post_translate().json()
    # identity fields are untouched
    assert card["id"] == CARD_ID
    assert card["url"] == STORED_CARD["url"]
    assert card["createdAt"] == STORED_CARD["createdAt"]
    # digest fields come from the fresh extraction + digest
    assert card["title"] == ARTICLE.title
    assert card["summary"] == EN_DIGEST.summary
    assert card["keyPoints"] == [
        {"takeaway": "First thought", "quote": "Long enough article text."},
        {"takeaway": "Second thought", "quote": None},
    ]
    assert card["tags"] == EN_DIGEST.tags
    assert card["category"] == EN_DIGEST.category


def test_happy_path_persists_exactly_what_the_client_gets(happy_wiring: list) -> None:
    response = post_translate()
    assert happy_wiring == [(CARD_ID, response.json())]


def test_extraction_uses_stored_card_url_and_digest_gets_target_language(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def fake_extract(url: str) -> ExtractedArticle:
        seen["url"] = url
        return ARTICLE

    def fake_digest(text: str, title: str | None = None, *, language: str = "uk") -> Digest:
        seen["text"] = text
        seen["title"] = title
        seen["language"] = language
        return EN_DIGEST

    monkeypatch.setattr(index, "get_card", lambda card_id: dict(STORED_CARD))
    monkeypatch.setattr(index, "extract_from_url", fake_extract)
    monkeypatch.setattr(index, "digest_text", fake_digest)
    monkeypatch.setattr(index, "update_card", lambda card_id, card: None)
    assert post_translate(language="en").status_code == 200
    assert seen == {
        "url": STORED_CARD["url"],
        "text": ARTICLE.text,
        "title": ARTICLE.title,
        "language": "en",
    }


# --- 404 / validation -----------------------------------------------------------


def test_unknown_card_returns_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(index, "get_card", lambda card_id: None)
    response = post_translate("no-such-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Card not found."}


@pytest.mark.parametrize("language", ["de", "UA", "ukrainian", "", 42, None])
def test_unsupported_language_returns_422(
    happy_wiring: list, language: object
) -> None:
    assert post_translate(language=language).status_code == 422


def test_missing_language_returns_422(happy_wiring: list) -> None:
    response = client.post(f"/api/cards/{CARD_ID}/translate", json={})
    assert response.status_code == 422


# --- error mapping ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (FetchError(), 502),
        (NotHtmlError(), 422),
        (EmptyExtractionError(), 422),
    ],
    ids=["fetch-502", "not-html-422", "empty-extraction-422"],
)
def test_extraction_errors_map_like_digest_route(
    monkeypatch: pytest.MonkeyPatch, error: Exception, status: int
) -> None:
    monkeypatch.setattr(index, "get_card", lambda card_id: dict(STORED_CARD))
    monkeypatch.setattr(index, "extract_from_url", _raise(error))
    response = post_translate()
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
def test_digest_errors_map_like_digest_route(
    monkeypatch: pytest.MonkeyPatch, error: Exception, status: int
) -> None:
    monkeypatch.setattr(index, "get_card", lambda card_id: dict(STORED_CARD))
    monkeypatch.setattr(index, "extract_from_url", lambda url: ARTICLE)
    monkeypatch.setattr(index, "digest_text", _raise(error))
    response = post_translate()
    assert response.status_code == status
    assert response.json() == {"detail": str(error)}


def test_get_card_db_failure_maps_to_500(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        index, "get_card", _raise(DbError("The database is unavailable. Please try again."))
    )
    response = post_translate()
    assert response.status_code == 500
    assert response.json() == {"detail": "The database is unavailable. Please try again."}


def test_update_card_db_failure_maps_to_500(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(index, "get_card", lambda card_id: dict(STORED_CARD))
    monkeypatch.setattr(index, "extract_from_url", lambda url: ARTICLE)
    monkeypatch.setattr(
        index, "digest_text", lambda text, title=None, language="uk": EN_DIGEST
    )
    monkeypatch.setattr(
        index,
        "update_card",
        _raise(DbError("The database is unavailable. Please try again.")),
    )
    response = post_translate()
    assert response.status_code == 500
    assert response.json() == {"detail": "The database is unavailable. Please try again."}
