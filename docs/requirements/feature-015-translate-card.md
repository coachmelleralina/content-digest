# Feature 015 — Translate endpoint: re-explain an existing card in another language (issue #14)

## Story

As a reader, I want to re-explain an existing card in another language (uk / ru / en) so I can
share or re-read a digest without pasting the URL again. The card is re-digested from its
source URL in the target language and updated in place; the frontend per-card UA|RU|EN
switcher (issue #16) calls this endpoint.

## Scope

`api/schema.sql` (new `language` column), `api/db.py` (`language` in mappers + `get_card` +
`update_card`), `api/index.py` (`POST /api/cards/{id}/translate`, `language` in the digest
route's card), and their specs. No frontend changes, no changes to `digest.py` / `extract.py`.

## Acceptance criteria

1. **Schema.** `schema.sql` stays idempotent and appends
   `ALTER TABLE cards ADD COLUMN IF NOT EXISTS language text NOT NULL DEFAULT 'uk';`
   Existing rows are backfilled with `'uk'` by the default.
2. **Mappers.** `card_to_row` / `row_to_card` carry `language`. The row tuple / `_COLUMNS`
   order is `id, url, title, summary, key_points, tags, category, language, created_at`
   (`language` sits between `category` and `created_at`; `created_at` stays last).
3. **Queries.** `insert_card` persists `language`. New `get_card(card_id) -> dict | None`
   (camelCase card or `None` when the id does not exist). New
   `update_card(card_id, card) -> None` (UPDATE `title`, `summary`, `key_points`, `tags`,
   `category`, `language` WHERE id; `id`, `url`, `created_at` are never updated).
   psycopg errors map to `DbError` as everywhere else in `db.py`.
4. **Endpoint (FIXED contract — frontend #16 builds against it).**
   `POST /api/cards/{id}/translate`, body `{"language": "uk"|"ru"|"en"}` (required;
   anything else → 422 via pydantic `Literal`). Flow:
   - `get_card(id)` → unknown id → 404 `{"detail": "Card not found."}`;
   - `extract_from_url(card.url)` — fresh re-extraction; error mapping identical to
     `POST /api/digest` (`FetchError` → 502, `NotHtmlError`/`EmptyExtractionError` → 422);
   - `digest_text(text, title, language=target)` — error mapping identical to `/api/digest`
     (`DigestConfigError` → 500, `DigestApiError`/`DigestParseError` → 502);
   - update the row: `summary`, `keyPoints` (`{takeaway, quote}` objects), `tags`, `title`
     and `category` may refresh (the model re-runs), `language` = target;
     `id` / `url` / `createdAt` unchanged;
   - 200 → the FULL updated card JSON in camelCase INCLUDING `"language"`.
   `DbError` anywhere → 500. Quotes naturally stay in the article's original language
   (feature 014 digest contract).
5. **Language surfaces everywhere.** `POST /api/digest` saves the requested `language` on the
   card and returns it; `GET /api/cards` items include `"language"`.
6. **Specs first, no network / no live DB.** New `api/test_translate_route.py` monkeypatches
   the seams on the `index` module (same style as `test_digest_route.py`): happy path
   (200, full card, `language` field, `update_card` called with the right fields), 404
   unknown id, 422 bad/missing language, extraction error mapping (502/422), digest error
   mapping (502/500), `DbError` → 500. `test_db.py` mapper specs updated for `language`.
   Existing route specs updated only where the new `language` field breaks them.

## Out of scope

- Frontend switcher UI — issue #16 (parallel; consumes this contract).
- Caching translations / storing multiple languages per card (the card is overwritten).
- Re-digesting old cards that still have string keyPoints (they translate fine: the row is
  fully overwritten with the new object shape).

## Notes

- Translation is a re-digest of the source, not a text translation: the article is
  re-extracted and re-explained in the target language, so takeaways/tags/category may
  legitimately differ between languages.
- Live smoke against prod (translate a real card uk → en) is deferred to the orchestrator
  after merge + deploy: `DATABASE_URL` is unreadable outside deployments (feature 013).
