"""Spec for feature 011 — cards persistence routes (issue #9).

No live DB: db functions are monkeypatched on the index module, same seam style
as test_digest_route.py.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import index
from db import DbError
from digest import Digest
from extract import ExtractedArticle

client = TestClient(index.app, raise_server_exceptions=False)

CARD = {
    "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "url": "https://example.com/a",
    "title": "A Title",
    "summary": "A summary.",
    "keyPoints": ["one"],
    "tags": ["x"],
    "category": "Engineering",
    "createdAt": "2026-06-11T10:00:00+00:00",
}


# --- POST /api/digest persists the card ----------------------------------------


def test_digest_inserts_returned_card(monkeypatch: pytest.MonkeyPatch) -> None:
    inserted: list[dict] = []
    monkeypatch.setattr(
        index, "extract_from_url", lambda url: ExtractedArticle(title="T", text="x " * 100)
    )
    monkeypatch.setattr(
        index,
        "digest_text",
        lambda text, title=None: Digest(
            summary="s", key_points=["k"], tags=["t"], category="C"
        ),
    )
    monkeypatch.setattr(index, "insert_card", inserted.append)

    response = client.post("/api/digest", json={"url": "https://example.com/a"})
    assert response.status_code == 200
    assert len(inserted) == 1
    assert inserted[0] == response.json()  # what the client got is what was saved


def test_digest_db_failure_maps_to_500(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        index, "extract_from_url", lambda url: ExtractedArticle(title="T", text="x " * 100)
    )
    monkeypatch.setattr(
        index,
        "digest_text",
        lambda text, title=None: Digest(
            summary="s", key_points=["k"], tags=["t"], category="C"
        ),
    )

    def boom(card: dict) -> None:
        raise DbError("The database is unavailable. Please try again.")

    monkeypatch.setattr(index, "insert_card", boom)
    response = client.post("/api/digest", json={"url": "https://example.com/a"})
    assert response.status_code == 500
    assert response.json() == {"detail": "The database is unavailable. Please try again."}


# --- GET /api/cards -------------------------------------------------------------


def test_list_cards_returns_cards(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(index, "list_cards", lambda: [CARD])
    response = client.get("/api/cards")
    assert response.status_code == 200
    assert response.json() == [CARD]


def test_list_cards_db_failure_maps_to_500(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom() -> list[dict]:
        raise DbError("The database is unavailable. Please try again.")

    monkeypatch.setattr(index, "list_cards", boom)
    response = client.get("/api/cards")
    assert response.status_code == 500
    assert "detail" in response.json()


# --- DELETE /api/cards/{id} -----------------------------------------------------


def test_delete_existing_card_returns_204(monkeypatch: pytest.MonkeyPatch) -> None:
    deleted: list[str] = []

    def fake_delete(card_id: str) -> bool:
        deleted.append(card_id)
        return True

    monkeypatch.setattr(index, "delete_card", fake_delete)
    response = client.delete(f"/api/cards/{CARD['id']}")
    assert response.status_code == 204
    assert deleted == [CARD["id"]]


def test_delete_unknown_card_returns_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(index, "delete_card", lambda card_id: False)
    response = client.delete("/api/cards/no-such-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Card not found."}
