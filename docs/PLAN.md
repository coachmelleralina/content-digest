# PLAN — Content Digest (empty → MVP)

Concrete build plan for the MVP described in [PRD.md](PRD.md).

> **Governance note:** this stack adds a backend (FastAPI), a database (Postgres), and external
> runtime deps (OpenRouter), superseding the bootstrap constraints. The decisions are now
> recorded: [ADR 002](decisions/002-backend-api-on-vercel.md) (root `api/` on Vercel),
> [ADR 003](decisions/003-postgres-storage.md) (Postgres from the start),
> [ADR 004](decisions/004-openrouter-ai.md) (OpenRouter, mid-tier model, AI-chosen categories).
> [constraints.md](constraints.md) is updated to match. Deployment is via the GitHub-connected
> Vercel project (push to `main` → Vercel builds).

## Stack

- **Frontend:** Vite + React + TypeScript (the existing `app/`). Talks to the backend over
  `fetch` to `/api/*`.
- **Backend:** minimal **Python FastAPI** service under `/api`, deployed as **Vercel** Python
  serverless functions. Handles extraction, the AI call, and DB reads/writes.
- **Storage:** **Postgres** (Vercel Postgres / Neon). One `cards` table.
- **AI:** **OpenRouter** — a single chat-completion call that returns summary, key points, tags,
  and a category for the extracted text.

Data flow: `paste URL → POST /api/digest → extract text → OpenRouter → store card in Postgres →
return card → frontend renders it on the board`. On load: `GET /api/cards → render sections`.

## Folder structure

```
content-digest/
  app/                      # Vite + React + TS frontend (existing)
    src/
      components/           # Board, Section, Card, UrlInput (render-only)
      lib/api.ts            # typed fetch wrappers for /api/*
  api/                      # Python FastAPI serverless (Vercel)
    index.py                # FastAPI app; routes: POST /api/digest, GET /api/cards, DELETE /api/cards/{id}
    extract.py              # URL → readable article text (pure)
    digest.py               # text → {summary, keyPoints[], tags[], category} via OpenRouter (pure)
    db.py                   # Postgres connection + cards queries
    schema.sql              # cards table DDL
    requirements.txt        # fastapi, httpx, psycopg, readability/trafilatura
  vercel.json               # build: static app/ + Python functions under /api
  .env.example              # OPENROUTER_API_KEY, DATABASE_URL (never commit .env)
  docs/                     # PRD, PLAN, requirements, decisions (ADRs), retros, constraints
```

`cards` (minimal): `id`, `url`, `title`, `summary`, `key_points` (jsonb), `tags` (jsonb),
`category`, `created_at`.

## Build steps (empty → MVP)

1. **Frontend shell (no AI yet).** Build the board UI from render-only components: `UrlInput`,
   `Board`, `Section`, `Card`. Drive it with mock card data and a typed `lib/api.ts`. Group
   cards into sections by `category`. *Done when:* the board renders mock cards in topic
   sections with loading/error states, spec-first per feature doc.
2. **FastAPI digest endpoint.** Write the three ADRs, then implement `POST /api/digest`:
   `extract.py` (URL → text) + `digest.py` (text → OpenRouter → summary/keyPoints/tags/category).
   Pure modules, unit-tested; the route just wires them. *Done when:* posting a URL returns a
   structured card JSON; bad URLs return a clear error, never a partial card.
3. **Postgres persistence.** Add `db.py` + `schema.sql`. `POST /api/digest` writes the card;
   add `GET /api/cards` and `DELETE /api/cards/{id}`. *Done when:* cards survive reload because
   the board loads from `GET /api/cards`.
4. **Wire frontend ↔ API.** Replace mocks: `UrlInput` calls `/api/digest`, board loads from
   `/api/cards`, delete calls the API. *Done when:* paste → real card appears in its category
   section and persists across reload, end to end on localhost.
5. **Deploy to Vercel.** Add `vercel.json`, set `OPENROUTER_API_KEY` + `DATABASE_URL` env vars,
   provision Postgres, run `schema.sql`. *Done when:* the deployed URL runs the full
   paste → digest → board → reload loop against the hosted DB.

Each step ships as its own `docs/requirements/feature-*.md` + failing spec + minimal code +
green test + commit + retro, per the repo working agreement.
