# Retrospective 014 — ELI5 digest (issue #13)

## What we did

Reworked the digest contract (feature 014): `summary` is now a 2–4-sentence ELI5 explanation
(no jargon, unavoidable terms explained in brackets); `key_points` became grounded
`{takeaway, quote}` objects — the takeaway is a simply-worded "what I take with me" thought in
the digest language, the quote a ≤12-word verbatim source fragment in the article's original
language, **verified code-side** (whitespace-normalized containment; hallucinated quotes →
`None`, takeaway kept); tags are canonical reusable topics normalized in code (strip,
lowercase, ≤24 chars, max 4 — truncate, never reject); `digest_text` gained
`language="uk" | "ru" | "en"` and the route accepts `{url, language?}` (default `uk`, other
values 422) and maps `key_points` → `keyPoints: [{takeaway, quote}]`. Spec-first: red shown as
two ImportErrors (`ALLOWED_LANGUAGES`, `KeyPoint`), then 88 pytest green.

## Live smoke (module-level, no DB)

`extract_from_url("https://en.wikipedia.org/wiki/Readability")` → `digest_text(language="uk")`:

```
summary[:200]: Readability це наскільки легко зрозуміти написаний текст, чи то книжка,
чи код програм. Він залежить від складності слів, довжини речень і оформлення, такого
як розмір шрифту. Якщо текст простий, людя…
- Читацький комфорт залежить від простоти слів і речень.
  quote_found=True 'Readability is the ease with which a reader can understand'
- У програмуванні коментарі та прості конструкції роблять код легшим для читання.
  quote_found=True 'In programming, things such as programmer comments,'
- Найпопулярніші друковані видання призначені для читачів з уровнем 9-го класу.
  quote_found=True 'The two publications with the largest circulations'
tags: ['читацькість', 'освіта', 'програмування']   category: Стиль письму
```

All three quotes survived verification on the first live call; tags came back lowercase and
canonical without needing the code-side fallback.

## What worked

- **Verification against the full original text, not the truncated prompt text** — the prompt
  sees a 12k-char subset, so checking the superset can never wrongly drop a model-copied quote.
- **Normalize, don't reject** for tags: a `mode="before"` pydantic validator running
  `normalize_tags` means sloppy model output (5 tags, mixed case) degrades gracefully instead
  of becoming a user-facing `DigestParseError`.
- Red was cheap and honest: the new-symbol ImportError collected both test modules as failures
  before a single line of implementation.

## What didn't / friction points

- `test_cards_routes.py` (outside the planned file set) constructed `Digest` with the old
  string `key_points` and a `digest_text` lambda without `language` — a contract change ripples
  into every fixture that builds the model. Minimal fixture update was unavoidable to keep the
  suite green.
- The live takeaway mixed one Russian word into Ukrainian («з уровнем» instead of «з рівнем») —
  model quality, not contract; acceptable for MVP, worth watching in #14 (translation reuses
  the same language plumbing).
- `Digest.tags` max_length must equal the normalizer's cap (both 4) or the validator order
  becomes load-bearing; kept them tied via the `MAX_TAGS` constant.

## Decisions to carry forward (for #14 / #15 / #16)

- **Response shape (frontend contract):** `keyPoints: [{takeaway: string, quote: string|null}]`
  — #16 builds `url#:~:text=<encoded quote>` links only when `quote` is non-null; #15 can rely
  on tags being lowercase, ≤24 chars, ≤4 per card; #14 sends `{url, language}` (or re-digests)
  with the same `uk|ru|en` literal.
- Old cards in the DB keep string keyPoints (jsonb); the frontend must tolerate both or the
  board can re-digest — decide in #14/#16.

## Changes made to CLAUDE.md / constraints / working agreement

- None required beyond TOC/state/log updates (deferred to merge session — this branch owns only
  the feature files per the issue scope).

## Open questions for next session

- Should `verify_quotes` also case-normalize? Kept case-sensitive to honor "verbatim,
  char-for-char" — revisit if live usage shows quotes dropped over case-only mismatches.
- Frontend handling of legacy string keyPoints (tolerate vs migrate).
