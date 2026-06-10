# Feature 004 — `api/` scaffold: FastAPI app + health route (issue #5)

## Story

As the developer building the Content Digest backend ([ADR 002](../decisions/002-backend-api-on-vercel.md),
PLAN step 2), I want a minimal FastAPI skeleton under `api/` with a health-check route and a
documented local-run workflow, so that subsequent backend features (digest endpoint, Postgres,
OpenRouter) land on a verified, runnable foundation instead of being the first Python code in
the repo.

## Scope

Skeleton only. One route, one test, local tooling docs. Structured the way Vercel's Python
runtime expects (module-level `app` ASGI variable in `api/index.py`).

## Acceptance criteria

1. `api/index.py` exposes a module-level FastAPI instance named `app` (Vercel Python runtime
   convention).
2. `GET /api/health` returns HTTP 200 with the exact JSON body `{"status": "ok"}`.
3. `api/test_health.py` covers AC 2 using FastAPI's `TestClient` under pytest, and was written
   (and shown failing) before the implementation existed — spec-first, adapted to Python.
4. `api/requirements.txt` pins runtime deps with compatible-release-style minimums:
   `fastapi`, `uvicorn` (local dev server), `httpx` (TestClient transport + future fetch use).
5. Dev-only deps (`pytest`) live in `api/requirements-dev.txt`, which includes the runtime
   file via `-r requirements.txt`, so Vercel installs only `requirements.txt`.
6. `api/README.md` documents: required Python version, venv setup, dependency install, local
   run via uvicorn, and a curl check for `/api/health`.
7. Root `.gitignore` covers `api/.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`; the venv
   is never committed.
8. Verified locally: pytest green inside the venv, and a live uvicorn process answers
   `curl http://127.0.0.1:<port>/api/health` with 200 `{"status":"ok"}`.

## Out of scope

- `POST /api/digest`, `extract.py`, `digest.py` — PLAN step 2 (separate issue).
- Postgres / `db.py` / `schema.sql` (ADR 003) — PLAN step 3.
- OpenRouter integration (ADR 004).
- `vercel.json` / deployment wiring — PLAN step 5.
- CORS configuration, error handling middleware, logging.
- Frontend changes of any kind.

## Preflight record

- Required: Python 3.10+ (Vercel Python runtime is 3.12).
- Found on this machine: system `python3` = **3.9.6** (Apple CLT) — below requirement.
- Remedy: installed Homebrew `python@3.12` → **Python 3.12.13** at
  `/opt/homebrew/bin/python3.12`; the venv and all verification below use it.
