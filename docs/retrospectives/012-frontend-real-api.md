# Retrospective 012 — Frontend on the real API (issue #10)

## What we did

Swapped the api client's internal layer per the feature-007 design: new `createHttpBackend()`
(fetch, `{detail}` → ApiError mapping, network failures → displayable message) selected for
dev/prod builds; vitest keeps the mock (`MODE === 'test'`), so all prior specs run unchanged.
Added the Vite dev proxy (`/api` → `127.0.0.1:8000`), a delete button on cards (callback prop
drilled Board → Section → Card; components stay render-only), and board-level error display in
`App` (load/delete failures via the pure `toErrorMessage`). 6 new specs for the HTTP backend
with stubbed `fetch` (red → green). 70 vitest green; lint/build clean.

## What worked

- The Backend seam from feature 007 paid off exactly as designed: zero changes to exported
  signatures or component code for the swap itself.
- E2E through the proxy verified the full path: Vite :5174 → FastAPI :8000, error bodies
  surfaced verbatim in the UI («The database is not configured…») — the error-path acceptance
  criterion passed against the real backend.

## What didn't / friction points

- **A Response body can only be consumed once** — my first error-mapping spec reused one
  mocked Response across two calls; second `json()` silently fell back to the generic message.
  Fixed with `mockImplementation` returning a fresh Response per call.
- Full visual e2e (paste → card on board → reload → delete) is blocked by the missing
  database: since feature 011, `POST /api/digest` persists before returning, so without
  `DATABASE_URL` even a successful AI digest ends as a clean 500. Expected; the remaining
  check rides on issue #9's live verification.

## Decisions to carry forward

- Mock backend stays only as the vitest backing; delete it when a DOM-testing layer (ADR
  required) makes component-level tests possible.
- "Move card between sections" (issue #10 original text) needs a backend category-edit
  endpoint — consciously out of scope here, tracked in the feature doc.

## Changes made to CLAUDE.md / constraints / working agreement

- CLAUDE.md TOC/state/log updated. No working-agreement changes.

## Open questions for next session

- After the DB lands: visual e2e in the browser, then close #9 and #10 together.
