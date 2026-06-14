"""Spec for feature 019 — POST /api/cards/{id}/similar route.

No network/DB: get_card / list_cards / find_similar are monkeypatched on index.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import index
from db import DbError
from similar import SimilarApiError, SimilarConfigError, SimilarParseError, SimilarRef

client = TestClient(index.app, raise_server_exceptions=False)

TARGET = {"id": "t-0", "title": "T", "summary": "s", "tags": ["x"], "language": "uk"}
OTHERS = [
    {"id": "c-1", "title": "A", "summary": "s", "tags": ["x"], "language": "uk"},
    {"id": "c-2", "title": "B", "summary": "s", "tags": ["y"], "language": "uk"},
]


def _wire(monkeypatch: pytest.MonkeyPatch, refs: list[SimilarRef]) -> dict:
    seen: dict = {}
    monkeypatch.setattr(index, "get_card", lambda cid: TARGET if cid == "t-0" else None)
    monkeypatch.setattr(index, "list_cards", lambda: [TARGET, *OTHERS])

    def fake_find(target, others, *, language="uk"):
        seen["others_ids"] = [o["id"] for o in others]
        seen["language"] = language
        return refs

    monkeypatch.setattr(index, "find_similar", fake_find)
    return seen


def test_returns_refs_and_excludes_self(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _wire(monkeypatch, [SimilarRef(id="c-1", reason="related")])
    response = client.post("/api/cards/t-0/similar")
    assert response.status_code == 200
    assert response.json() == [{"id": "c-1", "reason": "related"}]
    assert "t-0" not in seen["others_ids"]  # the target is not its own candidate
    assert seen["language"] == "uk"  # reason language follows the target card


def test_unknown_card_returns_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(index, "get_card", lambda cid: None)
    response = client.post("/api/cards/missing/similar")
    assert response.status_code == 404
    assert response.json() == {"detail": "Card not found."}


def test_empty_result_is_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    _wire(monkeypatch, [])
    response = client.post("/api/cards/t-0/similar")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (SimilarConfigError("not configured"), 500),
        (SimilarApiError("ai down", status=502), 502),
        (SimilarParseError("garbage"), 502),
    ],
    ids=["config-500", "api-502", "parse-502"],
)
def test_find_similar_errors_map(
    monkeypatch: pytest.MonkeyPatch, error: Exception, status: int
) -> None:
    monkeypatch.setattr(index, "get_card", lambda cid: TARGET)
    monkeypatch.setattr(index, "list_cards", lambda: [TARGET, *OTHERS])

    def boom(target, others, *, language="uk"):
        raise error

    monkeypatch.setattr(index, "find_similar", boom)
    response = client.post("/api/cards/t-0/similar")
    assert response.status_code == status
    assert response.json() == {"detail": str(error)}


def test_db_failure_maps_to_500(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(cid):
        raise DbError("The database is unavailable. Please try again.")

    monkeypatch.setattr(index, "get_card", boom)
    response = client.post("/api/cards/t-0/similar")
    assert response.status_code == 500
