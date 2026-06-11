# Feature 012 — Frontend on the real API (issue #10)

## User story

As a reader, I want the board to talk to the real backend, so that pasting a link produces a
real AI digest and my cards live in the database instead of an in-browser mock.

## Acceptance criteria

- GIVEN the dev servers (Vite + uvicorn) are running
  WHEN the frontend calls `digestUrl` / `listCards` / `deleteCard`
  THEN the requests hit `POST /api/digest`, `GET /api/cards`, `DELETE /api/cards/{id}` through
  the Vite dev proxy (`/api` → `http://127.0.0.1:8000`), same origin for the browser.
- GIVEN a backend error response `{detail: string}` with status N
  WHEN any client call fails
  THEN it rejects with `ApiError(detail, N)` and the UI shows the message (UrlInput inline for
  digest; a board-level notice for list/delete).
- GIVEN a network failure (server down)
  THEN calls reject with a user-displayable ApiError (no status).
- GIVEN a card on the board
  WHEN the user clicks its Delete button
  THEN `DELETE /api/cards/{id}` is called and the card leaves the board on success.
- Exported signatures of `lib/api.ts` are unchanged; only the internal Backend layer gains an
  HTTP implementation. Components stay render-only (delete is a callback prop; all state in
  `App`).
- Existing vitest suite stays green: tests keep running against the mock backend (vitest
  `MODE === 'test'`); new specs cover the HTTP backend with a stubbed `fetch`.

## Out of scope

- Moving cards between sections (no backend support yet — PRD P0 "move" arrives with a
  category-edit endpoint later; deletion + auto-grouping cover MVP board management for now).
- Optimistic updates, retries, caching.
- Removing the mock backend entirely (tests still use it; deleted when a DOM-testing layer
  exists).

## E2E verification

With uvicorn up: paste a real article URL in the browser → real digest card appears in its
category section. `GET /api/cards` on load and delete verified live once `DATABASE_URL`
exists (issue #9 live check) — until then they surface the clean 500 from the backend, which
is itself part of this feature's error-path acceptance.
