# Feature 010 — `POST /api/digest`: wire extract + digest with error handling (issue #8)

## Story

As the developer building the Content Digest backend (PLAN step 2), I want a thin
`POST /api/digest` route in `api/index.py` that wires the already-tested
`extract_from_url` (feature 008) and `digest_text` (feature 009) modules, so that posting an
article URL returns a complete card JSON in the exact frontend `Card` shape — and any failure
returns a clear, user-displayable error (PRD: never a blank/broken card).

## Scope

Route wiring only. No DB (issue #9), no frontend changes (issue #10), no new runtime
dependencies. The route stays thin: validation in a pydantic request model, error mapping in
exception handlers, business logic stays in `extract.py` / `digest.py`.

## API contract

`POST /api/digest` with JSON body `{"url": "<article url>"}`.

**Request validation** (pydantic model, FastAPI returns 422 on failure):

- `url` must be a non-empty string (whitespace-only rejected);
- `url` must parse with an `http` or `https` scheme and a non-empty host.

**Success — 200** with a card JSON in EXACTLY the frontend `Card` shape
([app/src/types.ts](../../app/src/types.ts)), camelCase:

```json
{
  "id": "<uuid4 string>",
  "url": "<echoed input url>",
  "title": "<extracted title>",
  "summary": "<AI summary>",
  "keyPoints": ["..."],
  "tags": ["..."],
  "category": "<AI-chosen label>",
  "createdAt": "<UTC ISO8601>"
}
```

The snake_case `key_points` from `Digest` maps to camelCase `keyPoints` here — this mapping
was explicitly deferred to the route layer (retro 009). The card is NOT persisted yet
(issue #9); the route just returns it.

**Errors** — every error body is `{"detail": "<user-displayable message>"}` (message taken
from the typed error's `str()` / `.message`):

| Error (module)                            | HTTP status |
| ----------------------------------------- | ----------- |
| `FetchError` (extract)                    | 502         |
| `NotHtmlError` (extract)                  | 422         |
| `EmptyExtractionError` (extract)          | 422         |
| `DigestConfigError` (digest)              | 500         |
| `DigestApiError` (digest)                 | 502         |
| `DigestParseError` (digest)               | 502         |
| Invalid request body (pydantic)           | 422         |

## `.env` loading

`api/index.py` loads `api/.env` at import time via a small stdlib helper (~10 lines): parse
`KEY=VALUE` lines (skip blanks/comments), set only variables not already present in the
environment. No `python-dotenv` dependency. This runs before any digest config is read
(`digest_text` reads `OPENROUTER_API_KEY` per call, so import-time loading is sufficient).
`api/.env` stays gitignored; on Vercel the env vars come from project settings and the file
is simply absent.

## Acceptance criteria

Spec-first pytest in `api/test_digest_route.py` using `fastapi.testclient.TestClient`, with
`extract_from_url` and `digest_text` monkeypatched (NO network in tests):

1. Happy path: 200; body has EXACTLY the 8 camelCase keys; `id` parses as a UUID;
   `createdAt` parses as ISO8601 UTC; `keyPoints` carries the digest's `key_points`;
   `url` echoes the input.
2. `FetchError` → 502 with `{"detail": <message>}`.
3. `NotHtmlError` → 422 with the error's message in `detail`.
4. `EmptyExtractionError` → 422 with the error's message in `detail`.
5. `DigestApiError` → 502 with the error's message in `detail`.
6. `DigestParseError` → 502 with the error's message in `detail`.
7. `DigestConfigError` → 500 with the error's message in `detail`.
8. Invalid bodies → 422: missing `url`, empty/whitespace `url`, non-http(s) scheme
   (`ftp://...`), scheme-less string.
9. Full `api/` pytest suite green (29 prior + new); tests are written and shown failing (red)
   before the implementation.

## Live smoke test (the one allowed network step)

After the suite is green: run uvicorn locally with the real `OPENROUTER_API_KEY` from
`api/.env`, POST a stable public article URL → expect 200 with a real digest; POST a
non-existent domain → expect 502 with a clean `detail`. Result recorded in the retro.

## Out of scope

- Postgres persistence, `GET /api/cards`, `DELETE /api/cards/{id}` — issue #9.
- Frontend swap from mock to real fetch — issue #10.
- Vercel deployment — issue #11.
- Category normalization of near-duplicate AI labels — accepted MVP gap (ADR 004).
