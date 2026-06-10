"""Content Digest backend — FastAPI app (feature 004, issue #5).

Vercel's Python runtime imports this module and serves the module-level `app`
ASGI variable. Keep `app` at module level; do not wrap it in a factory.
"""

from fastapi import FastAPI

app = FastAPI(title="content-digest api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
