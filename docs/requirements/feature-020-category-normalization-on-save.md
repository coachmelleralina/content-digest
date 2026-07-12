# Feature 020 — Category normalization on save (wiring for feature 002)

Closes GitHub issue [#12](https://github.com/coachmelleralina/content-digest/issues/12).

## Problem

Feature 002 shipped the pure module `app/src/lib/categories.ts` (`resolveCategory`) and the
board already merges near-duplicate sections at render time via `groupByCategory`. But the
**stored** category is still whatever free-form label the model proposed: the DB accumulates
"AI" / "Artificial Intelligence" / "machine  learning" variants. Anything that reads raw
cards (the similar-cards prompt, future exports, the API itself) sees split categories, and
the render-time merge is recomputed on every load instead of being settled once.

The actual save path turned out to be the backend (`POST /api/digest` inserts the card;
`POST /api/cards/{id}/translate` overwrites digest fields) — not a frontend save flow as
issue #12 originally assumed. So the wiring lives in `api/`, as a Python port of the same
rules.

## Scope

- `api/categories.py` — pure module exposing `resolve_category(raw: str, existing: list[str])
  -> str`, a faithful port of `app/src/lib/categories.ts` (same rules, same priority order,
  same guards; see feature-002 for the rule spec). The two implementations are kept in sync
  by porting the same spec cases.
- `db.list_categories()` — distinct stored category labels, ordered by first appearance
  (oldest section first) so resolution is deterministic and the earliest section's casing
  wins.
- Wiring in `api/index.py`:
  - `POST /api/digest`: resolve the model's category against `list_categories()` before
    `insert_card`.
  - `POST /api/cards/{id}/translate`: same resolution before `update_card`, so a re-digest
    cannot re-split a section.
  - A `DbError` while listing categories maps to 500 exactly like the neighbouring db calls.

Frontend `groupByCategory` stays as-is (harmless second line of defence for cards saved
before this feature).

## Acceptance criteria

- Digesting an article whose model-proposed category is a near-duplicate of an existing one
  (case/whitespace/hyphen, plural, acronym, single typo) stores the **existing** label
  verbatim; a genuinely new topic stores the cleaned-up new label.
- Translate keeps the card in its (resolved) section instead of re-introducing a raw label.
- Port fidelity: `api/test_categories.py` mirrors every case in
  `app/src/lib/categories.spec.ts`.
