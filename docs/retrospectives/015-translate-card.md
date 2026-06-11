# Retro 015 — translate card (issue #14)

## What was built

`POST /api/cards/{id}/translate` re-explains an existing card in `uk`/`ru`/`en`: fetch the
stored card → re-extract its source URL → `digest_text(language=target)` → overwrite the
card's digest fields in place. New `language` column (idempotent `ALTER TABLE ... ADD COLUMN
IF NOT EXISTS`, default `'uk'` backfills old rows), `get_card`/`update_card` in `db.py`,
`language` carried by both mappers (`_COLUMNS` order: `..., category, language, created_at` —
`language` between `category` and `created_at`, `created_at` stays last). `POST /api/digest`
now saves the request language on the card, so digest and list responses include
`"language"`. 88 → 108 pytest, all monkeypatch seams, no network/DB.

## What worked

- **Reusing the digest route's error-mapping contract verbatim.** The translate route is the
  digest route with `get_card` in front and `update_card` instead of `insert_card`; spec'ing
  it as "mapping identical to /api/digest" made both the tests and the implementation almost
  mechanical, and keeps the frontend (#16) facing one uniform error vocabulary.
- **Spec-first red was genuinely informative**: 14 failed + 10 errors enumerated exactly the
  missing surface (mappers without `language`, no `get_card`/`update_card` attributes on
  `index`, 404 route) before any implementation existed.
- **Fixed API contract up front** (camelCase card incl. `language`, 404 detail string,
  required-`language` body) — the parallel frontend agent (#16) could build against the spec
  file without waiting for this branch.

## What didn't / friction

- `update_card` reuses `card_to_row`, which demands the full card dict (including
  `createdAt`) even though UPDATE ignores `id`/`url`/`created_at`. Fine while routes always
  hold a full card; a partial-update helper would need a slimmer mapper.
- Existing-test blast radius was tiny but real: adding `language` to the digest card broke
  exactly two assertions in `test_digest_route.py` (`EXPECTED_KEYS`, contents test) —
  updated minimally, `test_cards_routes.py` needed no changes (its db seams are
  monkeypatched and shape-agnostic).
- Non-UUID `card_id` values reach Postgres and surface as `DbError` → 500 rather than 404
  (same pre-existing behavior as `DELETE /api/cards/{id}`). Acceptable for now; a shared
  uuid-validation guard for both routes is a small future cleanup.

## Deferred

- **Live smoke is deferred to the orchestrator on production** (after merge + deploy):
  `DATABASE_URL` exists only inside Vercel deployments (feature 013), so a local end-to-end
  translate against the real DB is impossible. Suggested prod smoke: `GET /api/cards` → pick
  a card id → `POST /api/cards/{id}/translate {"language":"en"}` → 200, English summary,
  `"language":"en"`, `id`/`url`/`createdAt` unchanged → `GET /api/cards` shows the updated
  card. Schema migration is self-applying on cold start (idempotent `ALTER TABLE`).

## Workflow changes proposed

- None structural. Note for future column additions: the `_COLUMNS` string in `db.py` is the
  single source of tuple order — change it, the two mappers, and `test_db.py`'s roundtrip
  fixture together, in one commit.
