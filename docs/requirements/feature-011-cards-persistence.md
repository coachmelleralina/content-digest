# Feature 011 — Cards persistence in Postgres (issue #9)

## User story

As a reader, I want my digested cards to be saved in the database, so that the board shows the
same cards after a reload or from another browser, instead of losing everything per session.

## Acceptance criteria

- GIVEN a successful `POST /api/digest`
  WHEN the card is returned to the client
  THEN the same card has been inserted into the `cards` table (same id and fields).
- GIVEN saved cards
  WHEN the client calls `GET /api/cards`
  THEN it receives all cards as camelCase card JSON, newest first.
- GIVEN an existing card id
  WHEN the client calls `DELETE /api/cards/{id}`
  THEN the row is removed and the response is 204; an unknown id returns 404 with
  `{"detail": "Card not found."}`.
- GIVEN `DATABASE_URL` is missing or the database is unreachable
  WHEN any DB-touching endpoint is called
  THEN the response is 500 with a clean user-displayable `{"detail": ...}` — never a stack
  trace (PRD: never a blank/broken card).
- Row↔card mapping lives in pure functions (`card_to_row` / `row_to_card`) unit-tested without
  a live database; route tests monkeypatch the db functions (no network, no DB in pytest).

## Schema (api/schema.sql — per ADR 003 / PLAN)

`cards(id uuid PK, url text, title text, summary text, key_points jsonb, tags jsonb,
category text, created_at timestamptz)`.

## Out of scope

- Pagination, search, updates (no PUT/PATCH).
- Category normalization on save (issue #12 — wired later).
- Connection pooling beyond psycopg defaults — serverless uses the provider's POOLED
  `DATABASE_URL` (ADR 003); one short-lived connection per request is acceptable at MVP scale.

## Live verification (deferred until a database exists)

The Vercel account has no Postgres store yet (checked via API at implementation time). When
`DATABASE_URL` lands in `api/.env`: run `python apply_schema.py`, start uvicorn, then
digest → list → delete against the real database. Recorded in the retro when done.

## Open questions

- None — provider choice (Vercel/Neon) doesn't affect code (ADR 003).
