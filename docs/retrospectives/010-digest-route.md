# Retrospective 010 — POST /api/digest route (issue #8)

## What we did

Wired the two existing pure modules into the first real endpoint: `POST /api/digest` validates
the request (pydantic, http/https only), runs `extract_from_url` → `digest_text`, and returns a
card in the frontend's exact camelCase shape (`keyPoints`, `createdAt`, uuid4 `id`). Error
mapping per the module contracts: FetchError → 502, NotHtml/EmptyExtraction → 422,
DigestConfigError → 500, DigestApi/DigestParse → 502 — always `{"detail": <user message>}`.
Added a stdlib-only `.env` loader (no python-dotenv dep). 17 new route tests (mocked wiring, no
network), then a live smoke test through uvicorn + curl. Sessions note: the implementing agent
hit its session limit after writing the req doc + tests; the orchestrator finished impl/retro.

## What worked

- Spec-first paid off again: the agent's tests fully pinned the route contract (key set, uuid
  version, ISO timestamp, every error mapping) before any implementation existed.
- The pure-module seams (`extract_from_url`, `digest_text`) made the route trivial — ~40 lines,
  and tests monkeypatch the seams directly.
- The smoke test caught two REAL bugs unit tests never would:
  1. **Wikipedia 403s httpx's default User-Agent.** Fixed in `extract.py` with a browser-like
     UA (test added, red→green).
  2. **The provided OpenRouter key is free-tier (no credits)** → HTTP 402 on the paid default
     model. Worked around via the ADR-004 `OPENROUTER_MODEL` env override pointing at a `:free`
     model locally; first free model hit a 429 rate limit, second succeeded.
- Error mapping was validated live three times for free (403 fetch, 402 and 429 from the AI) —
  each surfaced as a clean `{"detail": ...}` with the right status.

## What didn't / friction points

- Live smoke depends on third-party moods (UA blocks, free-tier 429s). Keep live checks out of
  pytest; they belong in this manual gate only.
- `anthropic/claude-3.5-haiku` as default is right per ADR 004, but local dev with a
  credit-less key requires the override — documented in `.env.example`.

## Decisions to carry forward

- Browser-like UA is now part of `fetch_html`'s contract (tested).
- `.env` loading is stdlib-only by design; revisit only if env handling grows.

## Changes made to CLAUDE.md / constraints / working agreement

- CLAUDE.md: feature-010 in TOC, Current state updated, this retro linked. No
  working-agreement changes.

## Open questions for next session

- Issue #9: persist the card (db.py owns serialization; route stays thin).
- For production (#11): either add OpenRouter credits for the paid default model or set
  `OPENROUTER_MODEL` to a free model in Vercel env vars.
