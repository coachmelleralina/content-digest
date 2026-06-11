"""Postgres access for cards (feature 011, issue #9; ADR 003).

One short-lived connection per call — serverless-friendly with the provider's
POOLED `DATABASE_URL`. Pure row<->card mappers are exported for tests; routes
only ever see camelCase card dicts.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

import psycopg


class DbError(Exception):
    """Base DB failure. str(error) is a user-displayable message."""


class DbConfigError(DbError):
    """DATABASE_URL is missing."""


_USER_MESSAGE = "The database is unavailable. Please try again."


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise DbConfigError(
            "The database is not configured (DATABASE_URL is missing)."
        )
    return url


# --- pure mappers ---------------------------------------------------------------


def card_to_row(card: dict[str, Any]) -> dict[str, str]:
    """camelCase card dict -> column dict with jsonb fields serialized."""
    return {
        "id": card["id"],
        "url": card["url"],
        "title": card["title"],
        "summary": card["summary"],
        "key_points": json.dumps(card["keyPoints"], ensure_ascii=False),
        "tags": json.dumps(card["tags"], ensure_ascii=False),
        "category": card["category"],
        "created_at": card["createdAt"],
    }


def row_to_card(row: Sequence[Any]) -> dict[str, Any]:
    """DB row (id, url, title, summary, key_points, tags, category, created_at)
    -> camelCase card dict. psycopg gives uuid.UUID / datetime / decoded jsonb."""
    id_, url, title, summary, key_points, tags, category, created_at = row
    return {
        "id": str(id_) if isinstance(id_, uuid.UUID) else id_,
        "url": url,
        "title": title,
        "summary": summary,
        "keyPoints": key_points,
        "tags": tags,
        "category": category,
        "createdAt": created_at.isoformat()
        if isinstance(created_at, datetime)
        else created_at,
    }


# --- queries ---------------------------------------------------------------------

_COLUMNS = "id, url, title, summary, key_points, tags, category, created_at"


def _connect() -> psycopg.Connection:
    try:
        return psycopg.connect(get_database_url(), connect_timeout=10)
    except DbConfigError:
        raise
    except psycopg.Error as exc:
        raise DbError(_USER_MESSAGE) from exc


def insert_card(card: dict[str, Any]) -> None:
    row = card_to_row(card)
    try:
        with _connect() as conn:
            conn.execute(
                f"INSERT INTO cards ({_COLUMNS}) "
                "VALUES (%(id)s, %(url)s, %(title)s, %(summary)s, "
                "%(key_points)s::jsonb, %(tags)s::jsonb, %(category)s, %(created_at)s)",
                row,
            )
    except psycopg.Error as exc:
        raise DbError(_USER_MESSAGE) from exc


def list_cards() -> list[dict[str, Any]]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM cards ORDER BY created_at DESC"
            ).fetchall()
    except psycopg.Error as exc:
        raise DbError(_USER_MESSAGE) from exc
    return [row_to_card(row) for row in rows]


def delete_card(card_id: str) -> bool:
    try:
        with _connect() as conn:
            result = conn.execute("DELETE FROM cards WHERE id = %s", (card_id,))
            return (result.rowcount or 0) > 0
    except psycopg.Error as exc:
        raise DbError(_USER_MESSAGE) from exc


def apply_schema() -> None:
    """Run schema.sql against DATABASE_URL (idempotent). Used by apply_schema.py."""
    sql = (Path(__file__).parent / "schema.sql").read_text()
    with _connect() as conn:
        conn.execute(sql)


if __name__ == "__main__":  # python db.py -> apply schema
    apply_schema()
    print("schema applied")
