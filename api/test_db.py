"""Spec for feature 011 — db.py pure mappers (issue #9). No live database."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

from db import DbConfigError, card_to_row, get_database_url, row_to_card

CARD = {
    "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "url": "https://example.com/a",
    "title": "A Title",
    "summary": "A summary.",
    "keyPoints": ["one", "two"],
    "tags": ["x", "y"],
    "category": "Engineering",
    "createdAt": "2026-06-11T10:00:00+00:00",
}


def test_card_to_row_produces_db_ready_values() -> None:
    row = card_to_row(CARD)
    assert row["id"] == CARD["id"]
    assert row["url"] == CARD["url"]
    assert row["title"] == CARD["title"]
    assert row["summary"] == CARD["summary"]
    assert json.loads(row["key_points"]) == ["one", "two"]  # jsonb as JSON text
    assert json.loads(row["tags"]) == ["x", "y"]
    assert row["category"] == CARD["category"]
    assert row["created_at"] == CARD["createdAt"]


def test_row_to_card_roundtrip() -> None:
    """A DB row (as psycopg returns it) maps back to the exact camelCase card."""
    db_row = (
        uuid.UUID(CARD["id"]),
        CARD["url"],
        CARD["title"],
        CARD["summary"],
        ["one", "two"],  # psycopg decodes jsonb to python lists
        ["x", "y"],
        CARD["category"],
        datetime(2026, 6, 11, 10, 0, 0, tzinfo=timezone.utc),
    )
    card = row_to_card(db_row)
    assert card == CARD


def test_get_database_url_missing_raises_config_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(DbConfigError):
        get_database_url()


def test_get_database_url_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    assert get_database_url() == "postgres://u:p@h/db"
