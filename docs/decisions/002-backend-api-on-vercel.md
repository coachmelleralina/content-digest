# ADR 002 — Backend service (`api/`) deployed on Vercel

## Status

Accepted.

## Context

The MVP ([PRD.md](../PRD.md), [PLAN.md](../PLAN.md)) needs server-side work that can't run
safely or reliably in the browser: fetching+extracting arbitrary article URLs (CORS, parsing),
calling the AI provider with a secret API key, and reading/writing the database. The bootstrap
constraint was "no backend in the app" — this ADR supersedes that for the MVP.

## Decision

- Add a minimal **Python FastAPI** service at the repo root under `api/`, deployed as **Vercel**
  Python serverless functions. Routes: `POST /api/digest`, `GET /api/cards`, `DELETE /api/cards/{id}`.
- The frontend (`app/`, Vite + React + TS) stays a static build and talks to the backend over
  `fetch` to `/api/*`. Deployment is via the **GitHub-connected Vercel project** (push to
  `main` → Vercel builds and deploys); no manual deploy step required.
- Secrets (`OPENROUTER_API_KEY`, `DATABASE_URL`) live only in Vercel env vars and local `.env`
  (gitignored); never shipped to the client.

## Consequences

- The repo is no longer frontend-only: app code now lives in **both** `app/` (frontend) and
  `api/` (backend). The "no app code outside `app/`" constraint is relaxed to allow `api/`;
  governance files still stay at the root.
- Vercel project setup: the frontend build output and the `api/` functions must both be wired
  (a root `vercel.json` added in PLAN Step 5). Until `api/` exists, the project deploys the
  frontend with **Root Directory = `app`**.
- Local dev now has two processes (Vite + the Python service); document the run commands when
  the backend lands.
- Python is a new toolchain — gate it behind its own preflight (see PLAN) before relying on it.
