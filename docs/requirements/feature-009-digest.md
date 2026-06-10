# Feature 009 — `api/digest.py`: text → summary/keyPoints/tags/category via OpenRouter (issue #7)

## Story

As the developer building the Content Digest backend ([ADR 004](../decisions/004-openrouter-ai.md),
PLAN step 2), I want a pure-ish `api/digest.py` module that turns extracted article text into a
structured digest (`summary`, `key_points[]`, `tags[]`, `category`) via a single OpenRouter
chat-completion call, so that issue #8 can wire `POST /api/digest` as a thin route over
already-tested logic.

## Scope

Module only. No route wiring (`api/index.py` untouched — issue #8), no extraction, no DB, no
real network calls in tests. One HTTP call per digest, strict-JSON-only prompting, robust
parsing, typed errors with user-displayable messages (PRD: never a blank/broken card).

## Acceptance criteria

1. `api/digest.py` exposes a pydantic model `Digest` with fields
   `summary: str`, `key_points: list[str]`, `tags: list[str]`, `category: str`, validated as:
   - `summary` non-empty (whitespace-only rejected);
   - `key_points` 1..8 items;
   - `tags` 1..6 items;
   - `category` non-empty and single-line (no newline characters). **Free-form** — the AI
     names the topic itself; no fixed category list (ADR 004).
2. Model id comes from the `OPENROUTER_MODEL` env var, defaulting to
   `"anthropic/claude-3.5-haiku"` (mid-tier balanced per ADR 004); swapping models is a
   one-line/env-only change. `OPENROUTER_API_KEY` is read from the environment; a missing or
   empty key raises a typed `DigestConfigError` with a clear message **before** any HTTP call.
3. `digest_text(text: str, title: str | None = None) -> Digest` makes exactly **one**
   chat-completion POST to `https://openrouter.ai/api/v1/chat/completions` via httpx. The
   prompt instructs strict-JSON-only output with exactly the keys
   `summary`, `key_points`, `tags`, `category`.
4. Input text is truncated to ~12,000 characters before prompting (cost bound). The
   truncation lives in a pure helper that is unit-tested directly.
5. Robust response parsing:
   - markdown code fences (```/```json) around the JSON are stripped before parsing;
   - non-JSON / malformed / schema-invalid model output raises a typed `DigestParseError`;
   - HTTP error statuses and network failures raise a typed `DigestApiError` carrying the
     HTTP status (when one exists).
   All digest errors carry a user-displayable message via `str(error)`.
6. `api/test_digest.py` covers, using `httpx.MockTransport` (no real API calls):
   happy path → `Digest`; code-fenced JSON → `Digest`; malformed JSON → `DigestParseError`;
   HTTP 500 → `DigestApiError` (status preserved); missing key → `DigestConfigError`;
   `Digest` validation failures (empty summary, 0/9 key points, 7 tags, multi-line category);
   truncation helper behaviour. Written and shown failing (red) before the implementation.
7. Full `api/` pytest suite green; no `.venv`/`__pycache__` tracked; no new runtime
   dependencies (httpx already in `requirements.txt`).

## Out of scope

- Wiring `POST /api/digest` in `api/index.py` — **issue #8**.
- **Live OpenRouter smoke test** — no API key is available in this environment; the real-call
  smoke test happens in **issue #8** (needs `OPENROUTER_API_KEY`, optionally
  `OPENROUTER_MODEL`, set locally / in Vercel).
- `extract.py` (URL → text) — issue #6.
- Postgres persistence — PLAN step 3.
- Category normalization/merging of near-duplicate AI labels — accepted MVP gap (ADR 004).

## Notes

- Tests inject an `httpx.Client` built on `MockTransport`; production calls construct a real
  client internally. Either way it is one POST per `digest_text` call.
- The response content is parsed tolerantly on the *wrapper* (fences) but strictly on the
  *schema* (exact keys, pydantic validation) — a digest either fully validates or raises a
  typed error; no partial cards.
