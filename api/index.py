"""Content Digest backend — FastAPI app (features 004 + 010, issues #5 + #8).

Vercel's Python runtime imports this module and serves the module-level `app`
ASGI variable. Keep `app` at module level; do not wrap it in a factory.
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

# On Vercel the entrypoint is imported by path (/var/task/api/index.py) and
# sys.path does NOT include this directory — sibling imports (db, digest,
# extract) need it. Locally (uvicorn from api/) this is a no-op.
sys.path.insert(0, str(Path(__file__).parent))

from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, field_validator

from db import (
    DbError,
    apply_schema,
    delete_card,
    get_card,
    insert_card,
    list_cards,
    update_card,
)
from digest import DigestApiError, DigestConfigError, DigestParseError, digest_text
from extract import EmptyExtractionError, FetchError, NotHtmlError, extract_from_url


def _load_dotenv() -> None:
    """Load KEY=VALUE lines from api/.env into os.environ (existing vars win).

    Stdlib-only on purpose — python-dotenv would be a new runtime dep (ADR rule).
    Runs at import time so digest config sees the key before the first request.
    """
    env_path = Path(__file__).parent / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

# Ensure-schema on cold start (feature 013): schema.sql is idempotent
# (CREATE TABLE IF NOT EXISTS), and Vercel's Neon DATABASE_URL is a sensitive
# env var readable only inside deployments — so the app self-initializes
# instead of relying on a manual migration step. Failure is non-fatal here;
# the request-path DbError mapping reports problems cleanly.
if os.environ.get("DATABASE_URL"):
    try:
        apply_schema()
    except Exception:  # noqa: BLE001 — never block startup on DDL
        pass

app = FastAPI(title="content-digest api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


class DigestRequest(BaseModel):
    url: str
    # Feature 014: digest language (explanation + takeaways); quotes stay in the
    # article's original language. Other values → 422 via pydantic.
    language: Literal["uk", "ru", "en"] = "uk"

    @field_validator("url")
    @classmethod
    def _http_url(cls, value: str) -> str:
        value = value.strip()
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("url must be an http(s) URL")
        return value


@app.post("/api/digest")
def digest_route(request: DigestRequest) -> dict[str, object]:
    try:
        article = extract_from_url(request.url)
    except FetchError as error:
        raise HTTPException(status_code=502, detail=error.message)
    except (NotHtmlError, EmptyExtractionError) as error:
        raise HTTPException(status_code=422, detail=error.message)

    try:
        digest = digest_text(article.text, title=article.title, language=request.language)
    except DigestConfigError as error:
        raise HTTPException(status_code=500, detail=str(error))
    except (DigestApiError, DigestParseError) as error:
        raise HTTPException(status_code=502, detail=str(error))

    card: dict[str, object] = {
        "id": str(uuid.uuid4()),
        "url": request.url,
        "title": article.title,
        "summary": digest.summary,
        # Feature 014: keyPoints are {takeaway, quote} objects (quote may be null)
        "keyPoints": [
            {"takeaway": point.takeaway, "quote": point.quote}
            for point in digest.key_points
        ],
        "tags": digest.tags,
        "category": digest.category,
        # Feature 015: the digest language is saved on the card
        "language": request.language,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    try:
        insert_card(card)
    except DbError as error:
        raise HTTPException(status_code=500, detail=str(error))
    return card


@app.get("/api/cards")
def cards_route() -> list[dict[str, object]]:
    try:
        return list_cards()
    except DbError as error:
        raise HTTPException(status_code=500, detail=str(error))


class TranslateRequest(BaseModel):
    # Feature 015 (issue #14): target digest language; required, no default.
    language: Literal["uk", "ru", "en"]


@app.post("/api/cards/{card_id}/translate")
def translate_card_route(card_id: str, request: TranslateRequest) -> dict[str, object]:
    """Re-explain an existing card in another language (feature 015, issue #14).

    Re-extracts the source URL, re-digests in the target language, and
    overwrites the card's digest fields. id / url / createdAt never change.
    """
    try:
        card = get_card(card_id)
    except DbError as error:
        raise HTTPException(status_code=500, detail=str(error))
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found.")

    try:
        article = extract_from_url(str(card["url"]))
    except FetchError as error:
        raise HTTPException(status_code=502, detail=error.message)
    except (NotHtmlError, EmptyExtractionError) as error:
        raise HTTPException(status_code=422, detail=error.message)

    try:
        digest = digest_text(article.text, title=article.title, language=request.language)
    except DigestConfigError as error:
        raise HTTPException(status_code=500, detail=str(error))
    except (DigestApiError, DigestParseError) as error:
        raise HTTPException(status_code=502, detail=str(error))

    updated: dict[str, object] = {
        **card,
        "title": article.title,
        "summary": digest.summary,
        "keyPoints": [
            {"takeaway": point.takeaway, "quote": point.quote}
            for point in digest.key_points
        ],
        "tags": digest.tags,
        "category": digest.category,
        "language": request.language,
    }
    try:
        update_card(card_id, updated)
    except DbError as error:
        raise HTTPException(status_code=500, detail=str(error))
    return updated


@app.delete("/api/cards/{card_id}", status_code=204)
def delete_card_route(card_id: str) -> Response:
    try:
        found = delete_card(card_id)
    except DbError as error:
        raise HTTPException(status_code=500, detail=str(error))
    if not found:
        raise HTTPException(status_code=404, detail="Card not found.")
    return Response(status_code=204)
