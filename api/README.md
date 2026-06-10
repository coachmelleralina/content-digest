# api/ — Content Digest backend (FastAPI on Vercel)

Minimal FastAPI service ([ADR 002](../docs/decisions/002-backend-api-on-vercel.md)). Vercel's
Python runtime serves the module-level `app` in [index.py](index.py); locally you run it with
uvicorn.

## Python version

**Python 3.10+ required; 3.12 recommended** (Vercel's Python runtime is 3.12). On macOS the
Apple CLT `python3` may be 3.9 — install a newer one, e.g. `brew install python@3.12`, and use
`python3.12` below.

## Setup (one-time, from `api/`)

```sh
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

For running the tests, install the dev set instead (it includes the runtime deps):

```sh
pip install -r requirements-dev.txt
```

Dependency layout: `requirements.txt` = runtime (what Vercel installs);
`requirements-dev.txt` = `-r requirements.txt` + pytest (local only).

## Run locally (from `api/`, venv active)

```sh
uvicorn index:app --host 127.0.0.1 --port 8000
```

Check it:

```sh
curl -i http://127.0.0.1:8000/api/health
# → HTTP/1.1 200 OK ... {"status":"ok"}
```

## Tests (from `api/`, venv active)

```sh
python -m pytest
```
