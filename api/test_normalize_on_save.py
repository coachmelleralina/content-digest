"""Spec for feature 020 — category normalization on save (issue #12).

The digest and translate routes resolve the model's free-form category against
the categories already stored (db.list_categories) before persisting, so near-
duplicate labels never create a new section. Same monkeypatch seam style as
test_digest_route.py / test_translate_route.py: no network, no live DB.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import index
from db import DbError
from digest import Digest, KeyPoint
from extract import ExtractedArticle

client = TestClient(index.app, raise_server_exceptions=False)

CARD_ID = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
STORED_CARD = {
    "id": CARD_ID,
    "url": "https://example.com/article",
    "title": "Original Title",
    "summary": "Проста відповідь: стаття про тестування.",
    "keyPoints": [{"takeaway": "Перша думка", "quote": "verbatim fragment"}],
    "tags": ["testing"],
    "category": "Startup",
    "language": "uk",
    "createdAt": "2026-06-10T09:00:00+00:00",
}
ARTICLE = ExtractedArticle(title="T", text="Long enough article text. " * 20)


def make_digest(category: str) -> Digest:
    return Digest(
        summary="s",
        key_points=[KeyPoint(takeaway="k", quote=None)],
        tags=["t"],
        category=category,
    )


def _raise(exc: Exception):
    def raiser(*args: object, **kwargs: object) -> object:
        raise exc

    return raiser


def wire_digest(
    monkeypatch: pytest.MonkeyPatch, category: str, existing: list[str]
) -> list[dict]:
    inserted: list[dict] = []
    monkeypatch.setattr(index, "extract_from_url", lambda url: ARTICLE)
    monkeypatch.setattr(
        index, "digest_text", lambda text, title=None, language="uk": make_digest(category)
    )
    monkeypatch.setattr(index, "list_categories", lambda: list(existing))
    monkeypatch.setattr(index, "insert_card", inserted.append)
    return inserted


# --- POST /api/digest -----------------------------------------------------------


def test_digest_files_near_duplicate_under_existing_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inserted = wire_digest(monkeypatch, " machine learning ", ["Machine Learning", "AI"])
    response = client.post("/api/digest", json={"url": "https://example.com/a"})
    assert response.status_code == 200
    assert response.json()["category"] == "Machine Learning"
    assert inserted[0]["category"] == "Machine Learning"  # stored, not just returned


def test_digest_keeps_genuinely_new_label(monkeypatch: pytest.MonkeyPatch) -> None:
    wire_digest(monkeypatch, "Web3", ["AI"])
    response = client.post("/api/digest", json={"url": "https://example.com/a"})
    assert response.status_code == 200
    assert response.json()["category"] == "Web3"


def test_digest_list_categories_db_failure_maps_to_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(index, "extract_from_url", lambda url: ARTICLE)
    monkeypatch.setattr(
        index, "digest_text", lambda text, title=None, language="uk": make_digest("AI")
    )
    monkeypatch.setattr(index, "list_categories", _raise(DbError("db down")))
    response = client.post("/api/digest", json={"url": "https://example.com/a"})
    assert response.status_code == 500
    assert response.json()["detail"] == "db down"


# --- POST /api/cards/{id}/translate ----------------------------------------------


def test_translate_resolves_category_against_existing_sections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updates: list[tuple[str, dict]] = []
    monkeypatch.setattr(index, "get_card", lambda card_id: dict(STORED_CARD))
    monkeypatch.setattr(index, "extract_from_url", lambda url: ARTICLE)
    monkeypatch.setattr(
        index,
        "digest_text",
        lambda text, title=None, language="uk": make_digest("Startups"),
    )
    monkeypatch.setattr(index, "list_categories", lambda: ["Startup", "AI"])
    monkeypatch.setattr(
        index, "update_card", lambda card_id, card: updates.append((card_id, card))
    )

    response = client.post(f"/api/cards/{CARD_ID}/translate", json={"language": "en"})
    assert response.status_code == 200
    assert response.json()["category"] == "Startup"  # stays in its section
    assert updates[0][1]["category"] == "Startup"
