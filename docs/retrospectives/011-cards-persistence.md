# Retrospective 011 — Cards persistence in Postgres (issue #9)

## What we did

Added the storage layer per ADR 003: `schema.sql` (idempotent `cards` table + created_at
index), `db.py` (pure `card_to_row`/`row_to_card` mappers, `insert_card`/`list_cards`/
`delete_card` with one short-lived connection per call, typed `DbError`/`DbConfigError` with
user-displayable messages, `apply_schema()` runnable as `python db.py`), and wired routes:
`POST /api/digest` now persists the card it returns, plus new `GET /api/cards` (newest first)
and `DELETE /api/cards/{id}` (204 / 404). psycopg[binary] added to requirements. Spec-first:
test_db.py (mappers, config) + test_cards_routes.py (route behavior, DB failures → clean 500)
written first, red (no `db` module) → green. 57 backend tests total.

## What worked

- The monkeypatch-the-index-seam pattern from feature 010 carried over cleanly to the three db
  functions — route tests stay network-free and DB-free.
- Pure mappers caught the shape decisions early (jsonb as JSON text on the way in, decoded
  lists on the way out; uuid/datetime → str at the boundary).

## What didn't / friction points

- **The user believed a Vercel database existed, but the account has none** (checked team and
  personal scopes via API: only a blob store for another project). Live verification
  (digest → saved → list → delete against real Postgres) is DEFERRED until `DATABASE_URL`
  exists in `api/.env`. The `apply_schema.py` path is ready (`python db.py`).
- Adding persistence to an existing route broke 5 prior route tests (they didn't mock
  `insert_card`) — expected coupling, fixed by extending the happy_wiring fixture; storage
  behavior is specced separately in test_cards_routes.py.

## Decisions to carry forward

- One connection per request is the MVP contract (serverless + provider's pooled URL); revisit
  only if latency data says so.

## Changes made to CLAUDE.md / constraints / working agreement

- CLAUDE.md TOC/state/log updated. No working-agreement changes.

## Open questions for next session

- Create the actual database (Vercel → Storage → Neon Postgres → connect to project
  `content-digest`), then: `vercel env pull`, put `DATABASE_URL` in `api/.env`,
  `python db.py`, and run the live digest→list→delete check before closing #9.
