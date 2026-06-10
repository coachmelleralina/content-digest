# Retro 004 — api/ scaffold (FastAPI health route, issue #5)

## What worked

- **Spec-first translated cleanly to Python.** `api/test_health.py` (pytest + FastAPI
  `TestClient`) was written before `index.py`; the red run failed with
  `ModuleNotFoundError: No module named 'index'`, then the minimal implementation turned it
  green (`1 passed in 0.16s`). Same loop as Vitest specs, different toolchain.
- **Preflight caught a real gap.** System `python3` was 3.9.6 (Apple CLT), below the 3.10+
  requirement. Installing Homebrew `python@3.12` (→ 3.12.13) matched the Vercel runtime
  exactly, so local verification runs on the same major version as production.
- **Two-file requirements split** (`requirements.txt` runtime, `requirements-dev.txt` =
  `-r requirements.txt` + pytest) keeps Vercel's install surface minimal while making local
  test setup one command.
- **Live verification, not just unit-green:** uvicorn on `127.0.0.1:8000` answered
  `GET /api/health` with `200 {"status":"ok"}` before the server was killed.

## What didn't

- The repo's Python ignore rules didn't exist until this feature — easy to commit a venv or
  `__pycache__/` by accident before the `.gitignore` update landed. Resolved in the same
  commit.
- `fastapi>=0.115` resolved to 0.136.3, which emits a `StarletteDeprecationWarning` about
  `httpx` vs the upcoming `httpx2` in `TestClient`. Harmless today; revisit pins when the
  digest endpoint lands.

## Workflow changes proposed

1. **CLAUDE.md "Common commands" needs a backend section** (venv setup, uvicorn run, pytest).
   This session ran in an isolated worktree under instructions not to edit `CLAUDE.md`; the
   exact lines were handed to the orchestrator to apply on merge — an allowed deviation from
   working-agreement rule 9, recorded here.
2. **Record the Python toolchain requirement** (3.10+ local, 3.12 on Vercel,
   `brew install python@3.12` on macOS where CLT python3 is 3.9) — captured in
   `api/README.md`; future backend issues should preflight against it before writing code.
