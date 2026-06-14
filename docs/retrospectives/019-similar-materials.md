# Retrospective 019 — Similar materials (find related cards)

## What we did

Shipped the "Похожие" button (feature 019, Variant A): one OpenRouter call ranks the user's
OTHER board cards by meaning and returns up to 3 with a one-line reason in the card's language.
Backend: `api/similar.py` (pure prompt builder + typed errors, reuses digest's OpenRouter
constants; filters returned ids to the real candidate set, dedupes, caps at 3, no AI call when
the board has no other cards) + `POST /api/cards/{id}/similar`. Frontend: pure
`lib/resolveSimilar.ts` (refs → display matches, drops ids no longer on the board), a bundled
`SimilarUiProps` prop forwarded Board→Section→Card, the button + inline results list, and
click-to-scroll-and-highlight in App. Spec-first throughout (red → green). 128 pytest + 103
vitest green; lint + build clean. **First feature built through the new PR flow (ADR 005).**

## What worked

- Reusing OpenRouter constants from `digest.py` kept `similar.py` small without a new shared
  module — minimal blast radius on the working digest path.
- Bundling the six new per-card props into one `SimilarUiProps` object kept Board/Section as
  one-line pass-throughs and Card render-only (it just derives its slice by id). Much cleaner
  than six flat props through three components.
- Id-filtering on BOTH sides (server filters to candidates; `resolveSimilar` re-checks against
  current cards) means a hallucinated or just-deleted id can never render.

## What didn't / friction points

- Local smoke impossible: the route reads the DB (`get_card`/`list_cards`) and local `.env`
  has no `DATABASE_URL` (sensitive, prod-only) — so the live check rides on the prod deploy,
  same gate as features 011/015.
- `similar.py` imports `DEFAULT_MODEL`/`OPENROUTER_URL`/`REQUEST_TIMEOUT_SECONDS` from
  `digest.py`; the two AI callers now share constants but duplicate the call/parse skeleton. A
  shared `openrouter.py` helper is the clean next step (P2) once a third caller appears.
- The third Card-fixture fan-out (api.spec/apiHttp.spec/route tests) still isn't a shared
  factory — backlog item R1 from IMPROVEMENTS.md is overdue.

## Decisions to carry forward

- Variant A (AI-ranks-the-board) is intentionally simple; swap `similar.py` for embeddings +
  pgvector (Variant B) only when boards grow large — it's a local change behind the same route.

## Changes to CLAUDE.md / constraints

- TOC + Current state + Self-improvement log updated. No working-agreement changes.

## Open questions for next session

- Prod smoke: create 2+ related cards, click "Похожие", confirm sensible top-3 + reasons, and
  that the jump scrolls/highlights.
- The three quality passes the user asked for (tag quality, explanation quality, design) are
  still queued as separate small PRs.
